"""
Configuration management for aidev
"""
import os
from pathlib import Path
from typing import Optional
from aidev.constants import (
    AIDEV_DIR,
    CONFIG_DIR,
    PROFILES_DIR,
    CUSTOM_PROFILES_DIR,
    MCP_SERVERS_DIR,
    CUSTOM_MCP_DIR,
    MEMORY_BANKS_DIR,
    PLUGINS_DIR,
    CACHE_DIR,
    LOGS_DIR,
    ENV_FILE,
    TOOLS_CONFIG,
    SUPPORTED_TOOLS,
)
from aidev.utils import ensure_dir, load_json, save_json, load_env, save_env

# Minimal MCP config used when no global config exists
DEFAULT_PROJECT_MCP_CONFIG = {
    "mcpServers": {
        "git": {"command": "git-mcp-server", "args": []},
        "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]},
    }
}


class ConfigManager:
    """Manages aidev configuration and directories"""

    def __init__(self) -> None:
        """Initialize config manager"""
        self.aidev_dir = AIDEV_DIR
        self.config_dir = CONFIG_DIR
        self.profiles_dir = PROFILES_DIR
        self.custom_profiles_dir = CUSTOM_PROFILES_DIR
        self.mcp_servers_dir = MCP_SERVERS_DIR
        self.custom_mcp_dir = CUSTOM_MCP_DIR
        self.memory_banks_dir = MEMORY_BANKS_DIR
        self.plugins_dir = PLUGINS_DIR
        self.cache_dir = CACHE_DIR
        self.logs_dir = LOGS_DIR
        self.env_file = ENV_FILE
        self.tools_config = TOOLS_CONFIG

    def init_directories(self) -> None:
        """Initialize all required directories"""
        directories = [
            self.aidev_dir,
            self.config_dir,
            self.profiles_dir,
            self.custom_profiles_dir,
            self.mcp_servers_dir,
            self.custom_mcp_dir,
            self.memory_banks_dir,
            self.plugins_dir,
            self.cache_dir,
            self.logs_dir,
        ]

        for directory in directories:
            ensure_dir(directory)

    def is_initialized(self) -> bool:
        """Check if aidev is initialized"""
        return self.aidev_dir.exists() and self.config_dir.exists()

    def get_env(self) -> dict[str, str]:
        """Get global environment variables"""
        return load_env(self.env_file)

    def set_env(self, key: str, value: str) -> None:
        """Set a global environment variable"""
        env_vars = self.get_env()
        env_vars[key] = value
        save_env(self.env_file, env_vars)

    def get_tools_config(self) -> dict:
        """Get tools configuration"""
        return load_json(self.tools_config, default={})

    def save_tools_config(self, config: dict) -> None:
        """Save tools configuration"""
        save_json(self.tools_config, config)

    def get_project_config_path(self, project_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Get project config directory if it exists

        Args:
            project_dir: Project directory (defaults to current directory)

        Returns:
            Path to project config directory or None if not initialized
        """
        if project_dir is None:
            project_dir = Path.cwd()

        config_path = project_dir / ".aidev"
        return config_path if config_path.exists() else None

    def init_project(self, project_dir: Optional[Path] = None, profile: str = "default") -> Path:
        """
        Initialize aidev in a project directory

        Args:
            project_dir: Project directory (defaults to current directory)
            profile: Default profile to use

        Returns:
            Path to created config directory
        """
        if project_dir is None:
            project_dir = Path.cwd()

        config_path = project_dir / ".aidev"
        ensure_dir(config_path)

        # Create config.json
        config_file = config_path / "config.json"
        if not config_file.exists():
            save_json(config_file, {"profile": profile, "environment": {}, "mcp_overrides": {}})

        # Create profile file
        profile_file = config_path / "profile"
        if not profile_file.exists():
            profile_file.write_text(profile)

        # Create .env file
        env_file = config_path / ".env"
        if not env_file.exists():
            env_file.touch()

        # Set up project-local tool config folders for legacy compatibility
        self._init_project_tool_configs(project_dir)

        return config_path

    def _init_project_tool_configs(self, project_dir: Path) -> None:
        """
        Create project-local .claude/.cursor folders with MCP configs or symlinks
        back to the user's global MCP config if available.
        """
        tool_dirs = [
            ("claude", ".claude", ".mcp.json"),
            ("cursor", ".cursor", "mcp.json"),
        ]

        for tool_id, folder_name, filename in tool_dirs:
            tool_def = SUPPORTED_TOOLS.get(tool_id)
            if not tool_def:
                continue

            global_config_path = Path(os.path.expanduser(tool_def["config_path"]))
            local_dir = project_dir / folder_name
            ensure_dir(local_dir)

            local_config_path = local_dir / filename
            if local_config_path.exists():
                # Respect existing files/symlinks
                continue

            if global_config_path.exists():
                try:
                    local_config_path.symlink_to(global_config_path)
                    continue
                except OSError:
                    # Fall back to writing a local file if symlinks are not permitted
                    pass

            # Write a minimal default MCP config if no global file or symlink failed
            save_json(local_config_path, DEFAULT_PROJECT_MCP_CONFIG)
