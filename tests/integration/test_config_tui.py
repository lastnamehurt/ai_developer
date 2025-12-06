"""
Smoke test for the config TUI to ensure it launches without crashing.
"""
from pathlib import Path

from aidev.tui_config import ProfileConfigApp
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager


def _temp_managers(tmp_path: Path) -> tuple[ConfigManager, ProfileManager, MCPManager]:
    base = tmp_path / "home" / ".aidev"

    config_manager = ConfigManager()
    config_manager.aidev_dir = base
    config_manager.config_dir = base / "config"
    config_manager.profiles_dir = config_manager.config_dir / "profiles"
    config_manager.custom_profiles_dir = config_manager.profiles_dir / "custom"
    config_manager.mcp_servers_dir = config_manager.config_dir / "mcp-servers"
    config_manager.custom_mcp_dir = config_manager.mcp_servers_dir / "custom"
    config_manager.memory_banks_dir = base / "memory-banks"
    config_manager.plugins_dir = base / "plugins"
    config_manager.cache_dir = base / "cache"
    config_manager.logs_dir = base / "logs"
    config_manager.env_file = base / ".env"
    config_manager.tools_config = config_manager.config_dir / "tools.json"

    profile_manager = ProfileManager()
    profile_manager.profiles_dir = config_manager.profiles_dir
    profile_manager.custom_profiles_dir = config_manager.custom_profiles_dir

    mcp_manager = MCPManager()
    mcp_manager.mcp_servers_dir = config_manager.mcp_servers_dir
    mcp_manager.custom_mcp_dir = config_manager.custom_mcp_dir
    mcp_manager.cache_dir = config_manager.cache_dir

    return config_manager, profile_manager, mcp_manager


def test_config_tui_smoke(tmp_path):
    config_manager, profile_manager, mcp_manager = _temp_managers(tmp_path)
    config_manager.init_directories()
    profile_manager.init_builtin_profiles()
    mcp_manager.init_builtin_servers()

    app = ProfileConfigApp(config_manager, profile_manager, mcp_manager)
    # Run briefly in headless test mode to ensure it starts
    with app.run_test() as pilot:
        pilot.pause()
