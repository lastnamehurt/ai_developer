"""
Textual TUI for browsing the MCP registry.
"""
from __future__ import annotations

import asyncio
from typing import Iterable, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Markdown, Static

from aidev.mcp import MCPManager
from aidev.models import MCPServerRegistry


def filter_registry_entries(
    entries: Iterable[MCPServerRegistry], query: str = "", tag: Optional[str] = None
) -> list[MCPServerRegistry]:
    """Filter registry entries by query and optional tag."""
    query_lower = (query or "").strip().lower()
    tag_lower = tag.lower() if tag else None

    filtered: list[MCPServerRegistry] = []
    for entry in entries:
        if tag_lower and tag_lower not in {t.lower() for t in entry.tags}:
            continue

        if query_lower:
            haystacks = [
                entry.name.lower(),
                entry.description.lower(),
                entry.author.lower(),
                " ".join(entry.tags).lower(),
            ]
            if not any(query_lower in h for h in haystacks):
                continue

        filtered.append(entry)

    return sorted(filtered, key=lambda e: e.name.lower())


class MCPBrowserApp(App):
    """TUI for browsing, filtering, and installing MCP servers."""

    CSS_PATH = "tui_mcp_browser.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("r", "refresh_registry", "Refresh"),
        Binding("i", "install_selected", "Install"),
    ]

    def __init__(self, mcp_manager: Optional[MCPManager] = None, refresh_on_start: bool = False) -> None:
        super().__init__()
        self.mcp_manager = mcp_manager or MCPManager()
        self.registry: list[MCPServerRegistry] = []
        self.filtered: list[MCPServerRegistry] = []
        self.installed: set[str] = set()
        self.selected_tag: Optional[str] = None
        self.refresh_on_start = refresh_on_start

    def compose(self) -> ComposeResult:
        """Build layout."""
        yield Header(show_clock=False)
        yield Footer()
        with Container():
            with Horizontal(id="filters"):
                yield Input(placeholder="Search (/, Enter)", id="search")
                yield DataTable(id="tag-table", zebra_stripes=True)
                yield Button("Refresh", id="refresh-btn", variant="default")
            with Horizontal():
                with Vertical(id="left"):
                    table = DataTable(id="registry-table", zebra_stripes=True)
                    table.add_columns("Name", "Version", "Stage", "Tags", "Install")
                    yield table
                with Vertical(id="right"):
                    yield Static("Details", classes="panel-title")
                    yield Markdown("", id="details")
                    yield Button("Install (i)", id="install-btn", variant="primary")
                    yield Static("", id="status")

    async def on_mount(self) -> None:
        """Load registry and focus search."""
        await self._refresh_registry(force=self.refresh_on_start)
        self.query_one("#search", Input).focus()

    async def _refresh_registry(self, force: bool = False) -> None:
        """Fetch registry and populate UI."""
        status = self.query_one("#status", Static)
        status.update("Loading registry...")
        try:
            entries = await asyncio.to_thread(self.mcp_manager.fetch_registry, force)
            self.registry = entries
            self.installed = set(self.mcp_manager.list_installed())
            self._populate_tags()
            self._apply_filters()
            status.update(f"Loaded {len(entries)} servers")
        except Exception as exc:  # pragma: no cover - defensive
            status.update(f"[red]Failed to load registry: {exc}[/red]")

    def _populate_tags(self) -> None:
        """Populate tag table from registry entries."""
        table = self.query_one("#tag-table", DataTable)
        table.clear()
        table.add_column("Tags")
        table.add_row("All", key="__all__")
        tags = sorted({tag for entry in self.registry for tag in entry.tags})
        for tag in tags:
            table.add_row(tag, key=tag)
        table.cursor_coordinate = (0, 0)
        self.selected_tag = None

    def _apply_filters(self) -> None:
        """Apply search/tag filters to registry list."""
        search_value = self.query_one("#search", Input).value or ""
        active_tag = None if not self.selected_tag or self.selected_tag == "__all__" else self.selected_tag
        self.filtered = filter_registry_entries(self.registry, search_value, active_tag)

        table = self.query_one("#registry-table", DataTable)
        table.clear()
        for entry in self.filtered:
            tags = ", ".join(entry.tags) if entry.tags else "-"
            stage_label = (entry.status or "unknown").lower()
            stage_cell = Text(stage_label, style=self._status_style(stage_label))
            icon = self._icon_for_entry(entry)
            name_cell = f"{icon} {entry.name}"

            if entry.name in self.installed:
                status_cell = Text("✓ installed", style="mcp-installed")
            else:
                status_cell = Text("available", style="mcp-available")

            table.add_row(name_cell, entry.version or "-", stage_cell, tags, status_cell, key=entry.name)

        if table.row_count:
            table.cursor_coordinate = (0, 0)
            self._update_details(self.filtered[0])
        else:
            self.query_one("#details", Markdown).update("No results.")

    def _current_entry(self) -> Optional[MCPServerRegistry]:
        """Get the currently highlighted entry."""
        table = self.query_one("#registry-table", DataTable)
        if table.cursor_coordinate is None or not self.filtered:
            return None
        row, _ = table.cursor_coordinate
        if 0 <= row < len(self.filtered):
            return self.filtered[row]
        return None

    def _update_details(self, entry: MCPServerRegistry) -> None:
        """Render details for the selected entry."""
        tags = ", ".join(entry.tags) if entry.tags else "-"
        profiles = ", ".join(entry.compatible_profiles) if entry.compatible_profiles else "-"
        install_cmd = entry.install.get("command", "")
        repo = entry.repository or "-"

        status_line = "✅ Installed" if entry.name in self.installed else "⬇️ Available to install"
        stage = entry.status or "unknown"

        body = (
            f"### {entry.name}\n\n"
            f"{entry.description}\n\n"
            f"{status_line} — **Stage:** `{stage}`\n\n"
            f"- **Author:** `{entry.author}`\n"
            f"- **Version:** `{entry.version}`\n"
            f"- **Tags:** {tags or '-'}\n"
            f"- **Profiles:** {profiles or '-'}\n"
            f"- **Repository:** {repo}\n\n"
        )

        if install_cmd:
            body += f"**Install command**\n\n```bash\n{install_cmd}\n```"

        self.query_one("#details", Markdown).update(body)

    def _icon_for_entry(self, entry: MCPServerRegistry) -> str:
        """Return a glyph based on common server names/tags."""
        name = entry.name.lower()
        tags = {t.lower() for t in entry.tags}

        if "github" in name:
            return ""
        if "gitlab" in name:
            return ""
        if "git" in name:
            return ""
        if "k8s" in name or "kubernetes" in tags:
            return "⎈"
        if "s3" in name:
            return "🪣"
        if "memory" in name:
            return "🧠"
        if "search" in name:
            return "🔍"
        if "logs" in name:
            return "📜"
        return "✨"

    def _status_style(self, status: str) -> str:
        """Map registry status to a style class."""
        status = status.lower()
        if status in {"stable", "verified"}:
            return "status-stable"
        if status in {"experimental", "beta"}:
            return "status-experimental"
        if status in {"deprecated"}:
            return "status-deprecated"
        if status in {"concept", "conceptual", "unavailable"}:
            return "status-concept"
        return ""

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update details when selection changes."""
        if event.table.id == "registry-table":
            entry = self._current_entry()
            if entry:
                self._update_details(entry)
        elif event.table.id == "tag-table":
            self.selected_tag = event.row_key if event.row_key != "__all__" else None
            self._apply_filters()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Live filter as search input changes."""
        if event.input.id == "search":
            self._apply_filters()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Button handlers."""
        if event.button.id == "refresh-btn":
            await self._refresh_registry(force=True)
        elif event.button.id == "install-btn":
            await self.action_install_selected()

    async def action_focus_search(self) -> None:
        """Focus search input."""
        self.query_one("#search", Input).focus()

    async def action_refresh_registry(self) -> None:
        """Refresh registry data."""
        await self._refresh_registry(force=True)

    async def action_install_selected(self) -> None:
        """Install the currently selected server."""
        entry = self._current_entry()
        status = self.query_one("#status", Static)
        if not entry:
            status.update("[yellow]No server selected[/yellow]")
            return

        status.update(f"Installing {entry.name}...")
        ok, stdout, stderr = await asyncio.to_thread(self.mcp_manager.install_server, entry.name, return_output=True)
        if ok:
            self.installed.add(entry.name)
            status.update(f"[green]✓ Installed {entry.name}[/green]")
            self._apply_filters()
        else:
            error_msg = stderr.strip() or stdout.strip() or "Unknown error"
            # Truncate to keep UI tidy
            if len(error_msg) > 160:
                error_msg = error_msg[:157] + "..."
            status.update(f"[red]Failed to install {entry.name}: {error_msg}[/red]")
