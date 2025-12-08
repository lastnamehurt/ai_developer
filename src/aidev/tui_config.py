"""
Textual-based TUI for editing profiles: toggle MCP servers, edit env bindings, and preview.
Shows profile details, global env vars, MCP servers, and profile-specific overrides.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Markdown, DataTable, Select, Static

from aidev.config import ConfigManager
from aidev.mcp import MCPManager
from aidev.models import MCPServerConfig, Profile
from aidev.profiles import ProfileManager
from aidev.env_requirements import (
    get_required_env_vars_for_profile,
    get_env_var_info,
    get_missing_env_vars,
)


class ProfileConfigApp(App):
    """TUI for profile configuration."""

    CSS_PATH = "tui_config.tcss"
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
        project_dir: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.config_manager = config_manager or ConfigManager()
        self.profile_manager = profile_manager or ProfileManager()
        self.mcp_manager = mcp_manager or MCPManager()
        self.current_profile_name: Optional[str] = None
        self.current_profile: Optional[Profile] = None
        self.project_dir = project_dir
        self.pending_warning: bool = False
        self.env_default_profile: Optional[str] = os.getenv("AIDEV_DEFAULT_PROFILE")

    def compose(self) -> ComposeResult:
        """Build layout with profile details, MCPs, and environment variables."""
        yield Header(show_clock=False)
        yield Footer()

        # Top section: Profile header with metadata
        with Vertical(id="profile-header-section"):
            yield Static("", id="profile-header", classes="panel-title")

        with Container():
            # Left: Profile selector and details
            with Vertical(id="left"):
                yield Static("Select Profile", classes="panel-title")
                yield Select(options=[], id="profile-select")

                yield Static("Profile Details", classes="panel-title")
                yield Markdown("", id="profile-info")

            # Middle: MCP Servers
            with Vertical(id="middle"):
                yield Static("MCP Servers (press 't' to toggle)", classes="panel-title")
                mcp_table = DataTable(id="mcp-table")
                mcp_table.add_columns("Name", "Status", "Description")
                yield mcp_table

            # Right: Environment Variables
            with Vertical(id="right"):
                yield Static("Global Environment Variables", classes="panel-title")
                env_table = DataTable(id="env-table")
                env_table.add_columns("Variable", "Status", "Value")
                yield env_table

                yield Static("Profile Environment Overrides", classes="panel-title")
                override_table = DataTable(id="override-table")
                override_table.add_columns("Key", "Value")
                yield override_table

                yield Input(placeholder="KEY", id="env-key")
                yield Input(placeholder="value", id="env-value")
                yield Button("Add/Update Env", id="env-apply", variant="primary")

                yield Static("Quick Actions", classes="panel-title")
                yield Markdown("**s** = save | **q** = quit | **t** = toggle MCP | **Enter** = apply env", id="help-text")

    async def on_mount(self) -> None:
        """Populate data at startup."""
        select = self.query_one("#profile-select", Select)
        profiles = self.profile_manager.list_profiles()
        select.set_options([(name, name) for name in profiles])
        if profiles:
            initial = (
                self.env_default_profile
                or self._active_project_profile()
                or ("default" if "default" in profiles else profiles[0])
            )
            await self.load_profile(initial)

    async def load_profile(self, name: str) -> None:
        """Load profile into widgets with full details."""
        profile = self.profile_manager.load_profile(name)
        if not profile:
            return
        self.current_profile_name = name
        self.current_profile = profile

        # Update profile selector
        select = self.query_one("#profile-select", Select)
        select.value = name

        # Update profile header
        header_text = f"Profile: [bold cyan]{name}[/bold cyan]"
        if self.project_dir:
            header_text += f" | Project: [dim]{self.project_dir}[/dim]"
        self.query_one("#profile-header", Static).update(header_text)

        # Update profile details (description, tags, extends, etc.)
        self._update_profile_info(profile, name)

        # Update MCP servers table
        self._update_mcp_table(profile)

        # Update global environment variables table
        self._update_env_table(profile)

        # Update profile overrides table
        self._update_override_table(profile)

        # Clear input fields
        self.query_one("#env-key", Input).value = ""
        self.query_one("#env-value", Input).value = ""

    def _update_profile_info(self, profile: Profile, name: str) -> None:
        """Update the profile details section."""
        info_parts = [f"**Name:** `{name}`"]

        if profile.description:
            info_parts.append(f"**Description:** {profile.description}")

        if profile.tags:
            tags = ", ".join(f"`{tag}`" for tag in profile.tags)
            info_parts.append(f"**Tags:** {tags}")

        if profile.extends:
            info_parts.append(f"**Extends:** `{profile.extends}`")

        # Show required env vars for this profile
        required_vars = get_required_env_vars_for_profile(profile)
        if required_vars:
            info_parts.append(f"**Required Env Vars:** {len(required_vars)}")
            for var in required_vars[:5]:  # Show first 5
                info_parts.append(f"  • `{var}`")
            if len(required_vars) > 5:
                info_parts.append(f"  • ... and {len(required_vars) - 5} more")

        # Show enabled MCP servers count
        enabled = [s for s in profile.mcp_servers if s.enabled]
        info_parts.append(f"**MCP Servers:** {len(enabled)}/{len(profile.mcp_servers)} enabled")

        markdown_text = "\n".join(info_parts)
        self.query_one("#profile-info", Markdown).update(markdown_text)

    def _update_mcp_table(self, profile: Profile) -> None:
        """Update the MCP servers table."""
        mcp_table = self.query_one("#mcp-table", DataTable)
        mcp_table.clear()

        for server in profile.mcp_servers:
            config = self.mcp_manager.get_server_config(server.name)
            desc = config.get("description", "") if config else "(unknown)"

            status = Text("● enabled", style="mcp-enabled") if server.enabled else Text("○ disabled", style="mcp-disabled")

            mcp_table.add_row(server.name, status, desc)

        if mcp_table.row_count:
            mcp_table.focus()
            mcp_table.cursor_coordinate = (0, 0)

    def _update_env_table(self, profile: Profile) -> None:
        """Update the global environment variables table with profile-required vars."""
        env_table = self.query_one("#env-table", DataTable)
        env_table.clear()

        # Get required env vars for this profile
        required_vars = get_required_env_vars_for_profile(profile)
        actual_env = self.config_manager.get_env()

        # Show required env vars and their status
        for var in sorted(required_vars):
            value = actual_env.get(var, "")
            if var == "GITHUB_PERSONAL_ACCESS_TOKEN" and not value:
                # Try alternative name
                value = actual_env.get("GITHUB_TOKEN", "")

            if value:
                status = Text("✓ set", style="env-ok")
                display_value = "***" if "TOKEN" in var or "KEY" in var or "PASSWORD" in var else value[:30]
            else:
                status = Text("✗ missing", style="env-missing")
                display_value = ""

            env_table.add_row(var, status, display_value)

        if env_table.row_count:
            env_table.cursor_coordinate = (0, 0)

    def _update_override_table(self, profile: Profile) -> None:
        """Update the profile-specific environment overrides table."""
        override_table = self.query_one("#override-table", DataTable)
        override_table.clear()

        for key, value in sorted(profile.environment.items()):
            override_table.add_row(key, value or "")

    def action_toggle_mcp(self) -> None:
        """Toggle selected MCP server enabled flag."""
        table = self.query_one("#mcp-table", DataTable)
        if table.cursor_coordinate is None or not self.current_profile:
            return
        row, _ = table.cursor_coordinate
        if row >= len(self.current_profile.mcp_servers):
            return

        # Use current profile data instead of DataTable API to avoid version differences
        server = self.current_profile.mcp_servers[row]
        name = server.name
        new_enabled = not server.enabled
        try:
            enabled_text = Text("● enabled", style="mcp-enabled") if new_enabled else Text("○ disabled", style="mcp-disabled")
            try:
                table.update_cell(row, "Enabled", enabled_text)
            except Exception:
                # Some Textual versions expect column index instead of label
                table.update_cell(row, 1, enabled_text)
        except Exception:
            # Fall back silently if table API changed; state is tracked on the profile object
            pass

        # Update in-memory profile
        updated_servers = []
        for server in self.current_profile.mcp_servers:
            if server.name == name:
                updated_servers.append(MCPServerConfig(name=server.name, enabled=new_enabled, config=server.config))
            else:
                updated_servers.append(server)
        self.current_profile.mcp_servers = updated_servers
        self._update_profile_info(self.current_profile, self.current_profile_name)

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
        self._update_override_table(self.current_profile)
        self._update_profile_info(self.current_profile, self.current_profile_name)
        key_input.value = ""
        val_input.value = ""

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
            self.notify("No profile selected", severity="error", timeout=3)
            return

        # Validate MCP server configs
        unknown = [
            s.name for s in self.current_profile.mcp_servers
            if not self.mcp_manager.get_server_config(s.name)
        ]

        warnings = []
        if unknown:
            warnings.append(f"Unknown MCP servers: {', '.join(unknown)}")

        if warnings and not self.pending_warning:
            warn_msg = "; ".join(warnings) + " - Press 's' again to confirm save"
            self.notify(warn_msg, severity="warning", timeout=5)
            self.pending_warning = True
            return

        self.pending_warning = False

        # Save as custom override to avoid mutating packaged profiles
        try:
            if self.project_dir:
                config_path = self.config_manager.init_project(
                    project_dir=Path(self.project_dir),
                    profile=self.current_profile_name
                )
                profile_file = config_path / "profile"
                profile_file.write_text(self.current_profile_name)

            self.profile_manager.save_profile(self.current_profile, custom=True)
            self.notify(
                f"✓ Saved profile '{self.current_profile_name}'",
                severity="information",
                timeout=2
            )
        except Exception as e:
            self.notify(f"Error saving profile: {e}", severity="error", timeout=5)

    def _active_project_profile(self) -> Optional[str]:
        """Detect active profile for current project."""
        if not self.project_dir:
            return None
        config_dir = self.config_manager.get_project_config_path(Path(self.project_dir))
        if not config_dir:
            return None
        profile_file = config_dir / "profile"
        if profile_file.exists():
            return profile_file.read_text().strip()
        return None


def run_tui() -> None:
    """Entry point for manual launching."""
    app = ProfileConfigApp(project_dir=str(Path.cwd()))
    app.run()
