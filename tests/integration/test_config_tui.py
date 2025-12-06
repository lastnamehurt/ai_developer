"""
Smoke test for the config TUI to ensure it launches without crashing.
"""
from pathlib import Path

import pytest

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


@pytest.mark.asyncio
async def test_config_tui_smoke(tmp_path):
    config_manager, profile_manager, mcp_manager = _temp_managers(tmp_path)
    config_manager.init_directories()
    profile_manager.init_builtin_profiles()
    mcp_manager.init_builtin_servers()

    app = ProfileConfigApp(config_manager, profile_manager, mcp_manager, project_dir=str(tmp_path / "project"))
    # Run briefly in headless test mode to ensure it starts and basic actions work
    async with app.run_test() as pilot:
        # Toggle first MCP server if present
        if app.current_profile and app.current_profile.mcp_servers:
            app.action_toggle_mcp()
        # Apply env change
        key_input = app.query_one("#env-key")
        val_input = app.query_one("#env-value")
        key_input.value = "TEST_KEY"
        val_input.value = "123"
        app.action_apply_env()
        # Attempt save (should not crash)
        app.action_save()
        pilot.pause()
    # Ensure env change is reflected in profile data
    assert app.current_profile is not None
    assert app.current_profile.environment.get("TEST_KEY") == "123"
