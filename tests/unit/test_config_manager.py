from pathlib import Path

from aidev.config import ConfigManager


def test_init_directories_sets_default_profile(tmp_path):
    """Ensure init_directories seeds default profile env variable without overriding existing."""
    cm = ConfigManager()
    cm.aidev_dir = tmp_path / ".aidev"
    cm.config_dir = cm.aidev_dir / "config"
    cm.profiles_dir = cm.config_dir / "profiles"
    cm.custom_profiles_dir = cm.profiles_dir / "custom"
    cm.mcp_servers_dir = cm.config_dir / "mcp-servers"
    cm.custom_mcp_dir = cm.mcp_servers_dir / "custom"
    cm.memory_banks_dir = cm.aidev_dir / "memory-banks"
    cm.plugins_dir = cm.aidev_dir / "plugins"
    cm.cache_dir = cm.aidev_dir / "cache"
    cm.logs_dir = cm.aidev_dir / "logs"
    cm.env_file = cm.aidev_dir / ".env"
    cm.tools_config = cm.config_dir / "tools.json"

    cm.init_directories()
    env_vars = cm.get_env()
    assert env_vars.get("AIDEV_DEFAULT_PROFILE") == "default"

    # Ensure existing value is preserved
    cm.set_env("AIDEV_DEFAULT_PROFILE", "custom")
    cm.init_directories()
    env_vars = cm.get_env()
    assert env_vars.get("AIDEV_DEFAULT_PROFILE") == "custom"

