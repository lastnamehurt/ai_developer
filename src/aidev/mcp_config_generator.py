"""
Generate MCP configuration files for AI tools
"""
import json
import os
import shutil
from pathlib import Path
import toml
from aidev.models import Profile
from aidev.mcp import MCPManager
from aidev.config import ConfigManager
from aidev.utils import ensure_dir, expand_env_vars, console


class MCPConfigGenerator:
    """Generates MCP configuration files for AI tools"""

    def __init__(self) -> None:
        """Initialize MCP config generator"""
        self.mcp_manager = MCPManager()
        self.config_manager = ConfigManager()

    def generate_config(self, tool_id: str, profile: Profile, config_path: Path) -> None:
        """
        Generate MCP configuration file for a tool

        Args:
            tool_id: Tool identifier (cursor, claude, etc.)
            profile: Profile to use for configuration
            config_path: Path to write the config file
        """
        console.print(f"[cyan]Generating MCP config for {tool_id}...[/cyan]")

        enabled_servers, disabled_servers = self._build_server_entries(profile)

        if tool_id == "codex":
            self._write_codex_config(config_path, enabled_servers, disabled_servers)
        elif tool_id == "gemini":
            self._write_gemini_config(config_path, enabled_servers, disabled_servers)
        else:
            self._write_standard_config(config_path, enabled_servers)

        console.print(f"[green]✓[/green] MCP config written to {config_path}")
        console.print(f"   Enabled {len(enabled_servers)} MCP servers")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _build_server_entries(
        self, profile: Profile
    ) -> tuple[dict[str, dict], set[str]]:
        """Build expanded MCP server entries for a profile"""
        global_env = self.config_manager.get_env()
        servers: dict[str, dict] = {}
        disabled: set[str] = set()

        for server_config in profile.mcp_servers:
            server_name = server_config.name

            if not server_config.enabled:
                disabled.add(server_name)
                continue

            server_def = self.mcp_manager.get_server_config(server_name)
            if not server_def:
                console.print(f"[yellow]Warning: MCP server '{server_name}' not found[/yellow]")
                continue

            # Base entry with commonly supported keys
            entry: dict[str, Optional[dict]] = {}
            for key in [
                "cwd",
                "url",
                "httpUrl",
                "http_url",  # allow snake-case, map later
                "bearer_token_env_var",
                "http_headers",
                "headers",
                "env_http_headers",
                "env_vars",
                "enabled_tools",
                "disabled_tools",
                "startup_timeout_sec",
                "tool_timeout_sec",
                "timeout",
                "trust",
                "description",
                "includeTools",
                "excludeTools",
            ]:
                if key in server_def:
                    entry[key] = server_def[key]

            # Resolve command path eagerly to avoid "No such file or directory"
            command = server_def.get("command")
            args = list(server_def.get("args", [])) if server_def.get("args") else []

            # Special handling for git: prefer git-mcp-go if available
            if server_name == "git" and command in (None, "git-mcp-server"):
                go_cmd = shutil.which("git-mcp-go")
                if go_cmd:
                    command = go_cmd
                    if not args:
                        args = ["serve", "-r", "."]

            if command:
                resolved_cmd = shutil.which(command)
                if not resolved_cmd and command == "npx":
                    # Common Homebrew locations for npm binaries
                    for candidate in ("/opt/homebrew/bin/npx", "/usr/local/bin/npx", "/usr/bin/npx"):
                        if Path(candidate).exists():
                            resolved_cmd = candidate
                            break
                entry["command"] = resolved_cmd or command
            if args:
                entry["args"] = args

            # Skip servers that have no runnable transport configured
            has_transport = any(
                [
                    entry.get("command"),
                    entry.get("url"),
                    entry.get("httpUrl"),
                    entry.get("http_url"),
                ]
            )
            if not has_transport:
                console.print(f"[yellow]Skipping MCP server '{server_name}' because no command/url/httpUrl is available[/yellow]")
                continue

            # Environment expansion
            if "env" in server_def:
                env_vars = {}
                for key, value in server_def["env"].items():
                    expanded_value = expand_env_vars(value, global_env)
                    expanded_value = expand_env_vars(expanded_value, profile.environment)
                    env_vars[key] = expanded_value
                entry["env"] = env_vars

            # Preserve autoApprove for tools that support it (non-Codex clients)
            if "autoApprove" in server_def:
                entry["autoApprove"] = server_def["autoApprove"]

            # Apply any profile-specific config overrides
            if server_config.config:
                entry["config"] = {**entry.get("config", {}), **server_config.config}

            # Sensible defaults to avoid startup/tool timeouts
            entry.setdefault("startup_timeout_sec", server_def.get("startup_timeout_sec", 30))
            entry.setdefault("tool_timeout_sec", server_def.get("tool_timeout_sec", 60))
            if "timeout" not in entry and "timeout" in server_def:
                entry["timeout"] = server_def["timeout"]

            servers[server_name] = entry

        return servers, disabled

    def _write_standard_config(self, config_path: Path, servers: dict[str, dict]) -> None:
        """Write legacy JSON configs used by Cursor/Claude/etc."""
        ensure_dir(config_path.parent)
        config = {"mcpServers": servers}
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _write_codex_config(
        self, config_path: Path, servers: dict[str, dict], disabled_servers: set[str]
    ) -> None:
        """
        Write Codex config.toml with [mcp_servers] entries, merging with existing settings
        and pruning disabled servers from the active profile.
        """
        ensure_dir(config_path.parent)

        existing: dict = {}
        if config_path.exists():
            try:
                existing = toml.load(config_path)
            except Exception as exc:  # pragma: no cover - defensive
                console.print(f"[yellow]Warning: Could not parse existing Codex config: {exc}[/yellow]")
                existing = {}

        # Start from existing config and merge MCP servers
        mcp_table = existing.get("mcp_servers", {})

        # Remove disabled servers from this profile
        for name in disabled_servers:
            mcp_table.pop(name, None)

        # Upsert enabled servers
        for name, data in servers.items():
            # Filter to Codex-supported keys; extra keys are ignored to avoid schema warnings
            filtered = {}
            for key in [
                "command",
                "args",
                "cwd",
                "url",
                "bearer_token_env_var",
                "http_headers",
                "env_http_headers",
                "env_vars",
                "env",
                "enabled_tools",
                "disabled_tools",
                "startup_timeout_sec",
                "tool_timeout_sec",
            ]:
                if key in data and data[key] is not None:
                    filtered[key] = data[key]
            mcp_table[name] = filtered

        existing["mcp_servers"] = mcp_table

        # Enable the Rust MCP client (required for HTTP/OAuth servers) unless explicitly set
        features = existing.get("features", {})
        features.setdefault("rmcp_client", True)
        existing["features"] = features

        with open(config_path, "w") as f:
            toml.dump(existing, f)

    def _write_gemini_config(
        self, config_path: Path, servers: dict[str, dict], disabled_servers: set[str]
    ) -> None:
        """
        Write Gemini CLI settings JSON with mcpServers merged.
        Location: ~/.gemini/settings.json
        """
        ensure_dir(config_path.parent)

        existing: dict = {}
        if config_path.exists():
            try:
                existing = json.loads(config_path.read_text())
            except Exception as exc:  # pragma: no cover - defensive
                console.print(f"[yellow]Warning: Could not parse existing Gemini config: {exc}[/yellow]")
                existing = {}

        mcp_table = existing.get("mcpServers", {})

        # Remove disabled servers
        for name in disabled_servers:
            mcp_table.pop(name, None)

        # Normalize and upsert servers
        for name, data in servers.items():
            normalized = {}
            for key, value in data.items():
                if value is None:
                    continue
                # Map snake_case to Gemini expected keys
                if key == "http_url":
                    normalized["httpUrl"] = value
                elif key == "http_headers":
                    normalized["headers"] = value
                elif key == "env_http_headers":
                    normalized["headers"] = {**normalized.get("headers", {}), **value}
                elif key == "env_vars":
                    normalized["env"] = {**normalized.get("env", {}), **{k: os.environ.get(k, "") for k in value}}
                else:
                    normalized[key] = value

            mcp_table[name] = normalized

        existing["mcpServers"] = mcp_table

        with open(config_path, "w") as f:
            json.dump(existing, f, indent=2)
