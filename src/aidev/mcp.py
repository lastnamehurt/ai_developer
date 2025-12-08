"""
MCP server management and registry
"""
import os
from pathlib import Path
from typing import Optional

import importlib.resources as pkg_resources
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
        try:
            self.fallback_registry = pkg_resources.files("aidev.examples") / "mcp-registry.json"
        except Exception:
            # Fallback to package-relative path
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
        data: list[dict] | None = None

        # Try cache first (when not forcing)
        if not force and self.registry_cache.exists():
            cached = load_json(self.registry_cache, default=[])
            if cached:
                normalized = self._normalize_registry_data(cached)
                try:
                    return [MCPServerRegistry(**item) for item in normalized]
                except Exception:
                    pass

        # Fetch from remote
        try:
            console.print("[cyan]Fetching MCP registry...[/cyan]")
            response = requests.get(self.registry_url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            console.print(f"[yellow]Registry fetch failed: {e} (using cache/fallback if available)[/yellow]")

        # If we got data from remote, cache and return it
        if data:
            normalized = self._normalize_registry_data(data)
            save_json(self.registry_cache, normalized)
            try:
                return [MCPServerRegistry(**item) for item in normalized]
            except Exception as exc:
                console.print(f"[yellow]Failed to parse fetched registry: {exc}[/yellow]")

        # Try cache again (covers cases where force=True but network failed)
        cached = load_json(self.registry_cache, default=[])
        if cached:
            normalized = self._normalize_registry_data(cached)
            try:
                return [MCPServerRegistry(**item) for item in normalized]
            except Exception:
                pass

        # Bundled fallback
        if self.fallback_registry.exists():
            console.print(f"[yellow]Using bundled fallback registry at {self.fallback_registry}[/yellow]")
            fallback = self._normalize_registry_data(load_json(self.fallback_registry, default=[]))
            try:
                return [MCPServerRegistry(**item) for item in fallback]
            except Exception:
                console.print("[yellow]Failed to parse bundled fallback registry.[/yellow]")

        return []

    def _normalize_registry_data(self, data: object) -> list[dict]:
        """
        Normalize registry data into a list of dicts suitable for MCPServerRegistry.
        Supports:
        - Legacy list format
        - New structured format with registry.verified / registry.conceptual
        """
        if isinstance(data, list):
            return data

        normalized: list[dict] = []
        if isinstance(data, dict) and isinstance(data.get("registry"), dict):
            registry = data["registry"]
            sections = [
                ("verified", "stable"),
                ("conceptual", "concept"),
            ]
            for section, default_status in sections:
                entries = registry.get(section, {})
                if not isinstance(entries, dict):
                    continue
                for name, info in entries.items():
                    if not isinstance(info, dict):
                        continue
                    status = info.get("status") or default_status
                    description = info.get("description", "")
                    version = info.get("version", "")
                    repository = info.get("repository") or info.get("source") or ""
                    author = info.get("author", "")
                    package = info.get("package", "")
                    endpoint = info.get("endpoint", "")
                    command = info.get("command", "")
                    tags = info.get("tags", [])
                    configuration = info.get("configuration", {})
                    compatible_profiles = info.get("compatible_profiles", [])
                    install = info.get("install", {})

                    # Build a best-effort install command if missing
                    if not install:
                        if package:
                            install = {"type": "npm", "command": f"npm install -g {package}"}
                        elif command:
                            install = {"type": "binary", "command": command}

                    normalized.append(
                        {
                            "name": name,
                            "description": description,
                            "author": author,
                            "repository": repository,
                            "version": version,
                            "install": install,
                            "configuration": configuration,
                            "tags": tags,
                            "compatible_profiles": compatible_profiles,
                            "status": status,
                            "package": package,
                            "source": info.get("source", ""),
                            "endpoint": endpoint,
                            "command": command,
                        }
                    )

        return normalized

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

    def install_server(self, name: str, *, return_output: bool = False):
        """
        Install an MCP server from registry

        Args:
            name: Server name
            return_output: When True, return (ok, stdout, stderr) instead of just bool

        Returns:
            True if installed successfully, False otherwise. When return_output=True,
            returns tuple (ok, stdout, stderr).
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
            return (False, "", "No installation command provided") if return_output else False

        # Parse and run command
        cmd_parts = install_cmd.split()
        return_code, stdout, stderr = run_command(cmd_parts)

        if return_code != 0:
            # Attempt a cargo --git fallback if crate is missing from registry
            fallback_tried = False
            fallback_stdout = ""
            fallback_stderr = ""
            if (
                install_type == "binary"
                and install_cmd.startswith("cargo install ")
                and server.repository
                and "could not find" in stderr.lower()
            ):
                fallback_tried = True
                console.print("[yellow]Primary install failed; trying cargo --git fallback...[/yellow]")
                fallback_cmd = ["cargo", "install", "--git", server.repository]
                return_code, fallback_stdout, fallback_stderr = run_command(fallback_cmd)

            if return_code != 0:
                combined_err = fallback_stderr or stderr
                console.print(f"[red]Installation failed: {combined_err}[/red]")
                if return_output:
                    combined_out = f"{stdout}\n{fallback_stdout}".strip()
                    return False, combined_out, combined_err
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
        return (True, stdout, stderr) if return_output else True

    def remove_server(self, name: str, profile_manager=None) -> bool:
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

        # Remove from profiles if a profile_manager is provided
        if profile_manager:
            for profile_name in profile_manager.list_profiles():
                profile = profile_manager.load_profile(profile_name)
                if not profile:
                    continue
                before = len(profile.mcp_servers)
                profile.mcp_servers = [s for s in profile.mcp_servers if s.name != name]
                if len(profile.mcp_servers) != before:
                    profile_manager.save_profile(profile, custom=True)
                    console.print(f"[yellow]Removed '{name}' from profile '{profile_name}'[/yellow]")
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

        # Ensure target directory exists
        self.mcp_servers_dir.mkdir(parents=True, exist_ok=True)

        # Copy bundled configs to user's mcp-servers directory
        import shutil
        copied_count = 0
        for config_file in bundled_configs_dir.glob("*.json"):
            target_path = self.mcp_servers_dir / config_file.name
            if not target_path.exists():
                shutil.copy(config_file, target_path)
                copied_count += 1

        if copied_count > 0:
            console.print(f"[dim]Installed {copied_count} MCP server configs[/dim]")

    def _get_bundled_configs_dir(self) -> Optional[Path]:
        """Get the bundled MCP server configs directory"""
        import sys

        # First, try development mode (installed with -e)
        try:
            module_path = Path(__file__).parent.parent.parent  # Go up to project root
            configs_dir = module_path / "configs" / "mcp-servers"
            if configs_dir.exists():
                return configs_dir
        except Exception:
            pass

        # Try using importlib.resources (works for installed packages)
        try:
            # For Python 3.9+
            if hasattr(pkg_resources, 'files'):
                configs_path = pkg_resources.files('aidev').joinpath('configs').joinpath('mcp-servers')
                if configs_path.is_dir():
                    # Convert to Path object
                    return Path(str(configs_path))
        except Exception:
            pass

        # Check if configs are installed with the package (PyInstaller bundle)
        if hasattr(sys, '_MEIPASS'):
            configs_dir = Path(sys._MEIPASS) / "configs" / "mcp-servers"
            if configs_dir.exists():
                return configs_dir

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
