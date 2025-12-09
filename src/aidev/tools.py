"""
AI tool detection and launching
"""
import os
import subprocess
from pathlib import Path
from typing import Optional
from aidev.constants import SUPPORTED_TOOLS
from aidev.models import ToolInfo
from aidev.utils import find_binary, console


class ToolManager:
    """Manages AI tool detection and launching"""

    def __init__(self) -> None:
        """Initialize tool manager"""
        self.supported_tools = SUPPORTED_TOOLS

    def detect_tool(self, tool_id: str) -> ToolInfo:
        """
        Detect if a tool is installed

        Args:
            tool_id: Tool identifier (e.g., 'cursor', 'claude', 'zed')

        Returns:
            ToolInfo with installation status
        """
        if tool_id not in self.supported_tools:
            raise ValueError(f"Unsupported tool: {tool_id}")

        tool_config = self.supported_tools[tool_id]
        tool_info = ToolInfo(
            name=tool_config["name"],
            binary=tool_config["binary"],
            app_name=tool_config["app_name"],
            config_path=Path(os.path.expanduser(tool_config["config_path"])),
        )

        # Check if binary exists
        binary_path = find_binary(tool_info.binary)
        if binary_path:
            tool_info.installed = True
            tool_info.version = self._get_version(tool_id, binary_path)

        return tool_info

    def detect_all_tools(self) -> dict[str, ToolInfo]:
        """
        Detect all supported AI tools

        Returns:
            Dictionary of tool_id -> ToolInfo
        """
        return {tool_id: self.detect_tool(tool_id) for tool_id in self.supported_tools}

    def get_tool_config_path(self, tool_id: str) -> Path:
        """
        Get the configuration path for a tool

        Args:
            tool_id: Tool identifier

        Returns:
            Path to tool's MCP configuration file
        """
        tool_info = self.detect_tool(tool_id)

        # Gemini supports per-project overrides at .gemini/settings.json
        if tool_id == "gemini":
            project_settings = self._find_project_gemini_settings()
            if project_settings:
                return project_settings

        return tool_info.config_path

    def launch_tool(
        self,
        tool_id: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        wait: bool = False,
    ) -> None:
        """
        Launch an AI tool

        Args:
            tool_id: Tool identifier
            args: Additional arguments to pass to the tool
            env: Environment variables to set
            wait: Whether to wait for the tool to exit
        """
        tool_info = self.detect_tool(tool_id)

        if not tool_info.installed:
            console.print(f"[red]Error: {tool_info.name} is not installed[/red]")
            console.print(f"Install {tool_info.name} from: {self._get_install_url(tool_id)}")
            return

        # Build command
        cmd = [tool_info.binary]
        if args:
            cmd.extend(args)

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        console.print(f"[cyan]Launching {tool_info.name}...[/cyan]")

        # Get current working directory
        cwd = os.getcwd()

        # Determine if this is an interactive CLI tool or GUI app
        # Treat Cursor as interactive CLI so its prompts stay attached to the user's terminal
        interactive_cli_tools = ["cursor", "claude", "codex", "gemini", "aider", "ollama"]
        is_interactive_cli = tool_id in interactive_cli_tools

        try:
            if is_interactive_cli:
                # For interactive CLI tools, exec directly (replace current process)
                # This keeps it attached to the terminal
                os.chdir(cwd)
                for key, value in process_env.items():
                    os.environ[key] = value
                os.execvp(tool_info.binary, cmd)
            elif wait:
                subprocess.run(cmd, env=process_env, cwd=cwd)
            else:
                # For GUI apps, launch in background
                subprocess.Popen(cmd, env=process_env, cwd=cwd, start_new_session=True)
        except Exception as e:
            console.print(f"[red]Error launching {tool_info.name}: {e}[/red]")

    def _get_version(self, tool_id: str, binary_path: Path) -> Optional[str]:
        """
        Get version of installed tool

        Args:
            tool_id: Tool identifier
            binary_path: Path to tool binary

        Returns:
            Version string or None
        """
        try:
            # Try common version flags
            for flag in ["--version", "-v", "version"]:
                result = subprocess.run(
                    [str(binary_path), flag],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        return None

    def _get_install_url(self, tool_id: str) -> str:
        """
        Get installation URL for a tool

        Args:
            tool_id: Tool identifier

        Returns:
            Installation URL
        """
        tool_config = self.supported_tools.get(tool_id)
        if tool_config and "install_url" in tool_config:
            return tool_config["install_url"]
        return "https://github.com"

    def _find_project_gemini_settings(self) -> Optional[Path]:
        """
        Find project-level Gemini settings.json (preferred over user-level).
        Searches from cwd upward for .gemini/settings.json.
        """
        cwd = Path.cwd()
        for path in [cwd, *cwd.parents]:
            candidate = path / ".gemini" / "settings.json"
            if candidate.exists():
                return candidate
            # Stop at home dir to avoid walking entire filesystem
            if path == Path.home():
                break

        # If not found and we are inside a project (detect .git or .aidev), create one at cwd/.gemini
        project_root = self._detect_project_root(cwd)
        if project_root:
            target = project_root / ".gemini" / "settings.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text('{ "mcpServers": {} }\n')
            return target
        return None

    def _detect_project_root(self, start: Path) -> Optional[Path]:
        """Detect a project root by looking for .git or .aidev markers."""
        for path in [start, *start.parents]:
            if (path / ".git").exists() or (path / ".aidev").exists():
                return path
            if path == Path.home():
                break
        return None
