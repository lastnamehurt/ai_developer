"""
Configuration management for aidev
"""
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
)
from aidev.utils import ensure_dir, load_json, save_json, load_env, save_env


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

        return config_path
