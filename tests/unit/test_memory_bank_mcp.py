
import pytest
from pathlib import Path
from aidev.mcp import MCPManager
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager

def _temp_managers(tmp_path: Path) -> tuple[MCPManager, ConfigManager, ProfileManager]:
    config_manager = ConfigManager()
    config_manager.aidev_dir = tmp_path / ".aidev"
    config_manager.config_dir = config_manager.aidev_dir / "config"
    config_manager.profiles_dir = config_manager.config_dir / "profiles"
    config_manager.custom_profiles_dir = config_manager.profiles_dir / "custom"
    config_manager.mcp_servers_dir = Path("src/aidev/configs/mcp-servers")
    config_manager.custom_mcp_dir = config_manager.mcp_servers_dir / "custom"
    config_manager.memory_banks_dir = config_manager.aidev_dir / "memory-banks"
    config_manager.plugins_dir = config_manager.aidev_dir / "plugins"
    config_manager.cache_dir = config_manager.aidev_dir / "cache"
    config_manager.logs_dir = config_manager.aidev_dir / "logs"
    config_manager.env_file = config_manager.aidev_dir / ".env"
    config_manager.tools_config = config_manager.config_dir / "tools.json"
    config_manager.init_directories()

    profile_manager = ProfileManager()
    profile_manager.profiles_dir = config_manager.profiles_dir
    profile_manager.custom_profiles_dir = config_manager.custom_profiles_dir
    profile_manager.init_builtin_profiles()

    mcp_manager = MCPManager()
    mcp_manager.mcp_servers_dir = config_manager.mcp_servers_dir
    mcp_manager.custom_mcp_dir = config_manager.custom_mcp_dir
    mcp_manager.cache_dir = config_manager.cache_dir
    mcp_manager.registry_cache = config_manager.cache_dir / "mcp-registry.json"
    mcp_manager.fallback_registry = Path(__file__).parent.parent / "examples" / "mcp-registry.json"

    return mcp_manager, config_manager, profile_manager

def test_memory_bank_server(tmp_path, monkeypatch):
    mcp_manager, _, _ = _temp_managers(tmp_path)
    result = mcp_manager.test_server("memory-bank")
    assert result is True
