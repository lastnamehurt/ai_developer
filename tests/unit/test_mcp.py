from pathlib import Path

import pytest

from aidev.mcp import MCPManager
from aidev.models import MCPServerRegistry
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager


def _temp_managers(tmp_path: Path) -> tuple[MCPManager, ConfigManager, ProfileManager]:
    config_manager = ConfigManager()
    config_manager.aidev_dir = tmp_path / ".aidev"
    config_manager.config_dir = config_manager.aidev_dir / "config"
    config_manager.profiles_dir = config_manager.config_dir / "profiles"
    config_manager.custom_profiles_dir = config_manager.profiles_dir / "custom"
    config_manager.mcp_servers_dir = config_manager.config_dir / "mcp-servers"
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


def test_registry_fallback_to_cache(tmp_path, monkeypatch):
    mcp_manager, _, _ = _temp_managers(tmp_path)
    # Populate cache
    registry_data = [
        {
            "name": "cached",
            "description": "cached",
            "author": "test",
            "repository": "",
            "version": "1.0.0",
            "install": {"type": "npm", "command": "echo ok"},
            "configuration": {},
            "tags": [],
        }
    ]
    mcp_manager.registry_cache.write_text(str(registry_data).replace("'", '"'))

    # Force failure
    monkeypatch.setattr(mcp_manager, "registry_url", "https://example.invalid/registry.json")
    entries = mcp_manager.fetch_registry(force=True)
    assert any(e.name == "cached" for e in entries)


def test_install_and_remove_updates_profiles(tmp_path, monkeypatch):
    mcp_manager, config_manager, profile_manager = _temp_managers(tmp_path)

    registry_entry = MCPServerRegistry(
        name="sample",
        description="test",
        author="me",
        repository="",
        version="0.1.0",
        install={"type": "npm", "command": "echo ok"},
        configuration={},
    )
    monkeypatch.setattr(mcp_manager, "fetch_registry", lambda force=False: [registry_entry])

    # Install
    assert mcp_manager.install_server("sample")
    # Enable in default profile
    profile = profile_manager.load_profile("default")
    profile.mcp_servers.append(profile.mcp_servers[0].__class__(name="sample", enabled=True))
    profile_manager.save_profile(profile, custom=True)

    # Remove
    custom_path = mcp_manager.custom_mcp_dir / "sample.json"
    assert custom_path.exists()
    mcp_manager.remove_server("sample")
    assert not custom_path.exists()
    updated = profile_manager.load_profile("default")
    assert all(s.name != "sample" for s in updated.mcp_servers)


@pytest.mark.parametrize(
    "config, expected",
    [
        ({"command": "echo", "args": ["ok"]}, True),
        ({"url": "http://localhost:9"}, False),
        ({}, False),
    ],
)
def test_test_server(config, expected, tmp_path, monkeypatch):
    mcp_manager, _, _ = _temp_managers(tmp_path)
    mcp_manager.save_server_config("probe", config)
    if "url" in config:
        monkeypatch.setattr("requests.get", lambda url, timeout=5: type("Resp", (), {"status_code": 503})())
    result = mcp_manager.test_server("probe")
    assert result == expected
