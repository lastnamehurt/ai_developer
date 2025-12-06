"""
Textual-based TUI for editing profiles: toggle MCP servers, edit env bindings, and preview.
"""
from __future__ import annotations

from typing import Optional

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Markdown, DataTable, Select, Static

from aidev.config import ConfigManager
from aidev.mcp import MCPManager
from aidev.models import MCPServerConfig, Profile
from aidev.profiles import ProfileManager


class ProfileConfigApp(App):
    """TUI for profile configuration."""

    CSS_PATH = None
    BINDINGS = [
        Binding("s", "save", "Save"),
        Binding("q", "quit", "Quit"),
        Binding("t", "toggle_mcp", "Toggle MCP"),
        Binding("enter", "apply_env", "Apply env", show=False),
    ]

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        profile_manager: Optional[ProfileManager] = None,
        mcp_manager: Optional[MCPManager] = None,
    ) -> None:
        super().__init__()
        self.config_manager = config_manager or ConfigManager()
        self.profile_manager = profile_manager or ProfileManager()
        self.mcp_manager = mcp_manager or MCPManager()
        self.current_profile_name: Optional[str] = None
        self.current_profile: Optional[Profile] = None

    def compose(self) -> ComposeResult:
        """Build layout."""
        yield Header(show_clock=False)
        yield Footer()
        with Container():
            with Horizontal():
                with Vertical(id="left"):
                    yield Static("Profiles", classes="panel-title")
                    yield Select(options=[], id="profile-select")
                    yield Markdown("Press `t` to toggle MCP, `Enter` on env value to update, `s` to save.")
                with Vertical(id="middle"):
                    yield Static("MCP Servers", classes="panel-title")
                    mcp_table = DataTable(id="mcp-table")
                    mcp_table.add_columns("Name", "Enabled", "Description")
                    yield mcp_table
                with Vertical(id="right"):
                    yield Static("Environment", classes="panel-title")
                    env_table = DataTable(id="env-table")
                    env_table.add_columns("Key", "Value", "Status")
                    yield env_table
                    yield Input(placeholder="KEY", id="env-key")
                    yield Input(placeholder="value", id="env-value")
                    yield Button("Apply env", id="env-apply", variant="primary")
                    yield Static("Preview", classes="panel-title")
                    yield Markdown("", id="preview")

    async def on_mount(self) -> None:
        """Populate data at startup."""
        select = self.query_one("#profile-select", Select)
        profiles = self.profile_manager.list_profiles()
        select.set_options([(name, name) for name in profiles])
        if profiles:
            await self.load_profile(profiles[0])

    async def load_profile(self, name: str) -> None:
        """Load profile into widgets."""
        profile = self.profile_manager.load_profile(name)
        if not profile:
            return
        self.current_profile_name = name
        self.current_profile = profile

        select = self.query_one("#profile-select", Select)
        select.value = name

        mcp_table = self.query_one("#mcp-table", DataTable)
        mcp_table.clear()
        for server in profile.mcp_servers:
            desc = ""
            config = self.mcp_manager.get_server_config(server.name)
            if config:
                desc = config.get("description", "")
            mcp_table.add_row(server.name, "on" if server.enabled else "off", desc)
        if mcp_table.row_count:
            mcp_table.focus()
            mcp_table.cursor_coordinate = (0, 0)

        env_table = self.query_one("#env-table", DataTable)
        env_table.clear()
        for key, value in sorted(profile.environment.items()):
            status = "set" if value else "missing"
            env_table.add_row(key, value or "", status)
        if env_table.row_count:
            env_table.cursor_coordinate = (0, 0)

        self._refresh_preview()

    def action_toggle_mcp(self) -> None:
        """Toggle selected MCP server enabled flag."""
        table = self.query_one("#mcp-table", DataTable)
        if table.cursor_coordinate is None or not self.current_profile:
            return
        row, _ = table.cursor_coordinate
        name = table.get_cell_at(row, 0)
        enabled = table.get_cell_at(row, 1) == "on"
        new_enabled = not enabled
        table.update_cell(row, 1, "on" if new_enabled else "off")

        # Update in-memory profile
        updated_servers = []
        for server in self.current_profile.mcp_servers:
            if server.name == name:
                updated_servers.append(MCPServerConfig(name=server.name, enabled=new_enabled, config=server.config))
            else:
                updated_servers.append(server)
        self.current_profile.mcp_servers = updated_servers
        self._refresh_preview()

    def action_apply_env(self) -> None:
        """Apply env changes from inputs."""
        if not self.current_profile:
            return
        key_input = self.query_one("#env-key", Input)
        val_input = self.query_one("#env-value", Input)
        key = key_input.value.strip()
        if not key:
            return
        value = val_input.value
        self.current_profile.environment[key] = value
        self._reload_env_table()
        self._refresh_preview()

    def _reload_env_table(self) -> None:
        table = self.query_one("#env-table", DataTable)
        table.clear()
        for key, value in sorted(self.current_profile.environment.items()):
            status = "set" if value else "missing"
            table.add_row(key, value or "", status)

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle profile change selection."""
        await self.load_profile(event.value)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "env-apply":
            self.action_apply_env()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in {"env-key", "env-value"}:
            self.action_apply_env()

    def action_save(self) -> None:
        """Persist current profile."""
        if not self.current_profile or not self.current_profile_name:
            return

        # Validate env (warn on missing)
        missing = [k for k, v in self.current_profile.environment.items() if not v]
        if missing:
            warn = f"[yellow]Warning: missing values for {', '.join(missing)}[/yellow]"
            self.query_one("#preview", Markdown).update(warn)
            return

        # Save as custom override to avoid mutating packaged profiles
        self.profile_manager.save_profile(self.current_profile, custom=True)
        self.query_one("#preview", Markdown).update(f"[green]Saved profile '{self.current_profile_name}'[/green]")

    def _refresh_preview(self) -> None:
        """Update preview markdown."""
        if not self.current_profile or not self.current_profile_name:
            return
        enabled_servers = [s.name for s in self.current_profile.mcp_servers if s.enabled]
        env_lines = [f"- {k}: {'***' if v else '(missing)'}" for k, v in sorted(self.current_profile.environment.items())]
        text = f"""
**Profile:** {self.current_profile_name}

**MCP Servers (enabled):**
{', '.join(enabled_servers) if enabled_servers else 'None'}

**Env:**
{chr(10).join(env_lines) if env_lines else 'None'}
"""
        self.query_one("#preview", Markdown).update(text)


def run_tui() -> None:
    """Entry point for manual launching."""
    app = ProfileConfigApp()
    app.run()
