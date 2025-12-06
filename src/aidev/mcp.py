"""
MCP server management and registry
"""
import os
from pathlib import Path
from typing import Optional

import requests

from aidev.constants import (
    MCP_SERVERS_DIR,
    CUSTOM_MCP_DIR,
    DEFAULT_MCP_REGISTRY,
    CACHE_DIR,
    CONFIGS_DIR,
)
from aidev.models import MCPServerRegistry
from aidev.utils import load_json, save_json, console, run_command


class MCPManager:
    """Manages MCP servers and registry"""

    def __init__(self) -> None:
        """Initialize MCP manager"""
        self.mcp_servers_dir = MCP_SERVERS_DIR
        self.custom_mcp_dir = CUSTOM_MCP_DIR
        self.cache_dir = CACHE_DIR
        self.registry_url = os.getenv("AIDEV_MCP_REGISTRY", DEFAULT_MCP_REGISTRY)
        self.registry_cache = self.cache_dir / "mcp-registry.json"
        self.fallback_registry = CONFIGS_DIR.parent / "examples" / "mcp-registry.json"

    def list_installed(self) -> list[str]:
        """
        List installed MCP servers

        Returns:
            List of MCP server names
        """
        servers = set()

        # Check built-in servers
        if self.mcp_servers_dir.exists():
            for path in self.mcp_servers_dir.glob("*.json"):
                servers.add(path.stem)

        # Check custom servers
        if self.custom_mcp_dir.exists():
            for path in self.custom_mcp_dir.glob("*.json"):
                servers.add(path.stem)

        return sorted(list(servers))

    def get_server_config(self, name: str) -> Optional[dict]:
        """
        Get MCP server configuration

        Args:
            name: Server name

        Returns:
            Server configuration dict or None
        """
        # Check custom first
        custom_path = self.custom_mcp_dir / f"{name}.json"
        if custom_path.exists():
            return load_json(custom_path)

        # Check built-in
        builtin_path = self.mcp_servers_dir / f"{name}.json"
        if builtin_path.exists():
            return load_json(builtin_path)

        return None

    def save_server_config(self, name: str, config: dict, custom: bool = True) -> None:
        """
        Save MCP server configuration

        Args:
            name: Server name
            config: Server configuration
            custom: Whether to save as custom server
        """
        if custom:
            path = self.custom_mcp_dir / f"{name}.json"
        else:
            path = self.mcp_servers_dir / f"{name}.json"

        save_json(path, config)

    def fetch_registry(self, force: bool = False) -> list[MCPServerRegistry]:
        """
        Fetch MCP server registry

        Args:
            force: Force refresh from remote

        Returns:
            List of registry entries
        """
        # Try cache first
        if not force and self.registry_cache.exists():
            data = load_json(self.registry_cache)
            if data:
                try:
                    return [MCPServerRegistry(**item) for item in data]
                except Exception:
                    pass

        # Fetch from remote
        try:
            console.print("[cyan]Fetching MCP registry...[/cyan]")
            response = requests.get(self.registry_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            save_json(self.registry_cache, data)

            return [MCPServerRegistry(**item) for item in data]
        except Exception as e:
            console.print(f"[yellow]Registry fetch failed: {e} (using cache/fallback if available)[/yellow]")
            cached = load_json(self.registry_cache, default=[])
            if cached:
                try:
                    return [MCPServerRegistry(**item) for item in cached]
                except Exception:
                    pass
            if self.fallback_registry.exists():
                fallback = load_json(self.fallback_registry, default=[])
                try:
                    return [MCPServerRegistry(**item) for item in fallback]
                except Exception:
                    pass
            return []

    def search_registry(self, query: str) -> list[MCPServerRegistry]:
        """
        Search MCP server registry

        Args:
            query: Search query

        Returns:
            List of matching registry entries
        """
        registry = self.fetch_registry()
        query_lower = query.lower()

        return [
            server
            for server in registry
            if query_lower in server.name.lower()
            or query_lower in server.description.lower()
            or any(query_lower in tag.lower() for tag in server.tags)
        ]

    def install_server(self, name: str) -> bool:
        """
        Install an MCP server from registry

        Args:
            name: Server name

        Returns:
            True if installed successfully, False otherwise
        """
        # Search registry for server
        registry = self.fetch_registry()
        server = next((s for s in registry if s.name == name), None)

        if not server:
            console.print(f"[red]Server '{name}' not found in registry[/red]")
            return False

        console.print(f"[cyan]Installing {server.name}...[/cyan]")
        console.print(f"Description: {server.description}")
        console.print(f"Author: {server.author}")

        # Execute installation command
        install_type = server.install.get("type", "npm")
        install_cmd = server.install.get("command", "")

        if not install_cmd:
            console.print("[red]No installation command provided[/red]")
            return False

        # Parse and run command
        cmd_parts = install_cmd.split()
        return_code, stdout, stderr = run_command(cmd_parts)

        if return_code != 0:
            console.print(f"[red]Installation failed: {stderr}[/red]")
            return False

        # Save server configuration
        config = {
            "name": server.name,
            "description": server.description,
            "version": server.version,
            "repository": server.repository,
            "configuration": server.configuration,
        }
        self.save_server_config(server.name, config)

        console.print(f"[green]✓[/green] Installed {server.name}")
        return True

    def remove_server(self, name: str) -> bool:
        """
        Remove an MCP server

        Args:
            name: Server name

        Returns:
            True if removed successfully, False otherwise
        """
        custom_path = self.custom_mcp_dir / f"{name}.json"
        if not custom_path.exists():
            console.print(f"[red]Server '{name}' not found[/red]")
            return False

        custom_path.unlink()
        console.print(f"[green]✓[/green] Removed {name}")
        return True

    def test_server(self, name: str) -> bool:
        """
        Test MCP server connectivity

        Args:
            name: Server name

        Returns:
            True if server is accessible, False otherwise
        """
        config = self.get_server_config(name)
        if not config:
            console.print(f"[red]Server '{name}' not found[/red]")
            return False

        console.print(f"[cyan]Testing {name}...[/cyan]")

        # Connectivity heuristic: check command/url availability
        command = config.get("command")
        url = config.get("url") or config.get("httpUrl") or config.get("http_url")
        args = config.get("args", [])

        if command:
            # Try to run a harmless command (e.g., --help) without failing hard
            probe_args = [command] + (args if args else ["--help"])
            code, out, err = run_command(probe_args, capture=True)
            if code != 0:
                console.print(f"[red]✗[/red] Command failed ({command}): {err or out}")
                console.print("[yellow]Hint:[/yellow] Ensure the binary is installed and on PATH.")
                return False
            console.print(f"[green]✓[/green] Command found and runnable: {command}")
        elif url:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code >= 400:
                    console.print(f"[red]✗[/red] HTTP {resp.status_code} from {url}")
                    console.print("[yellow]Hint:[/yellow] Check network/VPN and server URL.")
                    return False
                console.print(f"[green]✓[/green] HTTP reachable: {url}")
            except Exception as exc:  # pragma: no cover - network dependent
                console.print(f"[red]✗[/red] Request failed: {exc}")
                console.print("[yellow]Hint:[/yellow] Verify URL and network access.")
                return False
        else:
            console.print(f"[yellow]No command or URL to test for '{name}'.[/yellow]")
            return False

        return True

    def init_builtin_servers(self) -> None:
        """Initialize built-in MCP server configurations from bundled configs"""
        # Load built-in server configs from the bundled configs directory
        bundled_configs_dir = self._get_bundled_configs_dir()

        if not bundled_configs_dir or not bundled_configs_dir.exists():
            console.print("[yellow]Warning: Built-in MCP server configs not found[/yellow]")
            return

        # Copy bundled configs to user's mcp-servers directory
        import shutil
        for config_file in bundled_configs_dir.glob("*.json"):
            target_path = self.mcp_servers_dir / config_file.name
            if not target_path.exists():
                shutil.copy(config_file, target_path)

    def _get_bundled_configs_dir(self) -> Optional[Path]:
        """Get the bundled MCP server configs directory"""
        import sys

        # Check if we're in development mode (installed with -e)
        module_path = Path(__file__).parent.parent.parent  # Go up to project root
        configs_dir = module_path / "configs" / "mcp-servers"

        if configs_dir.exists():
            return configs_dir

        # Check if configs are installed with the package
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            return Path(sys._MEIPASS) / "configs" / "mcp-servers"

        return None

    def _get_builtin_servers(self) -> dict[str, dict]:
        """
        Load built-in MCP server configurations from JSON files

        This method is kept for compatibility but now loads from external JSON files
        instead of hardcoding configurations in Python.
        """
        bundled_configs_dir = self._get_bundled_configs_dir()

        if not bundled_configs_dir or not bundled_configs_dir.exists():
            return {}

        servers = {}
        for config_file in bundled_configs_dir.glob("*.json"):
            config = load_json(config_file)
            if config and "name" in config:
                servers[config["name"]] = config

        return servers
