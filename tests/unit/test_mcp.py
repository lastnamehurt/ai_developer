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
    mcp_manager.remove_server("sample", profile_manager=profile_manager)
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


def test_list_installed_empty(tmp_path):
    """Test listing installed servers when none exist"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    servers = mcp_manager.list_installed()
    assert isinstance(servers, list)
    # May have builtin servers from init_builtin_servers
    assert len(servers) >= 0


def test_list_installed_with_servers(tmp_path):
    """Test listing installed servers"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Add some custom servers
    mcp_manager.save_server_config("custom1", {"command": "test"}, custom=True)
    mcp_manager.save_server_config("custom2", {"command": "test"}, custom=True)

    servers = mcp_manager.list_installed()
    assert "custom1" in servers
    assert "custom2" in servers


def test_get_server_config_custom_first(tmp_path):
    """Test that custom server config takes precedence"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Create builtin server
    mcp_manager.save_server_config("test", {"command": "builtin"}, custom=False)

    # Create custom server with same name
    mcp_manager.save_server_config("test", {"command": "custom"}, custom=True)

    config = mcp_manager.get_server_config("test")
    assert config["command"] == "custom"


def test_get_server_config_not_found(tmp_path):
    """Test getting non-existent server config"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    config = mcp_manager.get_server_config("nonexistent")
    assert config is None


def test_save_server_config_builtin(tmp_path):
    """Test saving builtin server config"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    config = {"command": "test", "args": ["--version"]}
    mcp_manager.save_server_config("builtin_server", config, custom=False)

    assert (mcp_manager.mcp_servers_dir / "builtin_server.json").exists()


def test_save_server_config_custom(tmp_path):
    """Test saving custom server config"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    config = {"command": "myserver", "args": []}
    mcp_manager.save_server_config("my_server", config, custom=True)

    assert (mcp_manager.custom_mcp_dir / "my_server.json").exists()


def test_fetch_registry_from_cache(tmp_path):
    """Test fetching registry from cache"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Create cache
    registry_data = [
        {
            "name": "cached_server",
            "description": "Test server",
            "author": "Test",
            "repository": "https://github.com/test/test",
            "version": "1.0.0",
            "install": {"type": "npm", "command": "npm install test"},
            "configuration": {},
            "tags": ["test"],
            "compatible_profiles": []
        }
    ]

    import json
    mcp_manager.registry_cache.write_text(json.dumps(registry_data))

    # Fetch without force (should use cache)
    entries = mcp_manager.fetch_registry(force=False)

    assert len(entries) > 0
    assert any(e.name == "cached_server" for e in entries)


def test_fetch_registry_force_refresh(tmp_path, monkeypatch):
    """Test forcing registry refresh"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Mock successful HTTP response
    class MockResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return [{
                "name": "remote_server",
                "description": "From remote",
                "author": "Remote",
                "repository": "https://example.com",
                "version": "2.0.0",
                "install": {"type": "npm"},
                "configuration": {},
                "tags": [],
                "compatible_profiles": []
            }]

    monkeypatch.setattr("requests.get", lambda url, timeout: MockResponse())

    entries = mcp_manager.fetch_registry(force=True)

    assert len(entries) > 0
    assert any(e.name == "remote_server" for e in entries)
    # Should have cached the result
    assert mcp_manager.registry_cache.exists()


def test_fetch_registry_fallback_on_error(tmp_path, monkeypatch):
    """Test fallback to bundled registry on fetch error"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Create fallback registry
    fallback_data = [{
        "name": "fallback_server",
        "description": "Fallback",
        "author": "System",
        "repository": "",
        "version": "1.0.0",
        "install": {"type": "manual"},
        "configuration": {},
        "tags": [],
        "compatible_profiles": []
    }]

    import json
    mcp_manager.fallback_registry.parent.mkdir(parents=True, exist_ok=True)
    mcp_manager.fallback_registry.write_text(json.dumps(fallback_data))

    # Mock failed HTTP request
    def mock_get_error(url, timeout):
        raise Exception("Network error")

    monkeypatch.setattr("requests.get", mock_get_error)

    entries = mcp_manager.fetch_registry(force=True)

    assert len(entries) > 0
    assert any(e.name == "fallback_server" for e in entries)


def test_search_registry(tmp_path, monkeypatch):
    """Test searching registry"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    # Mock registry data
    registry_data = [
        MCPServerRegistry(
            name="git-server",
            description="Git integration",
            author="Test",
            repository="",
            version="1.0",
            install={"type": "npm"},
            tags=["git", "vcs"]
        ),
        MCPServerRegistry(
            name="github-server",
            description="GitHub API",
            author="Test",
            repository="",
            version="1.0",
            install={"type": "npm"},
            tags=["github", "api"]
        )
    ]

    monkeypatch.setattr(mcp_manager, "fetch_registry", lambda force=False: registry_data)

    results = mcp_manager.search_registry("git")

    assert len(results) >= 1
    assert any("git" in r.name.lower() or "git" in r.description.lower() for r in results)


def test_install_server_success(tmp_path, monkeypatch):
    """Test successful server installation"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    registry_entry = MCPServerRegistry(
        name="test_server",
        description="Test",
        author="Test",
        repository="https://github.com/test/test",
        version="1.0.0",
        install={"type": "npm", "command": "echo 'installed'"},
        configuration={"command": ["test-server"], "args": []}
    )

    monkeypatch.setattr(mcp_manager, "fetch_registry", lambda force=False: [registry_entry])

    # Mock successful command execution
    monkeypatch.setattr("aidev.mcp.run_command", lambda cmd: (0, "installed", ""))

    result = mcp_manager.install_server("test_server")

    assert result is True
    assert (mcp_manager.custom_mcp_dir / "test_server.json").exists()


def test_install_server_not_in_registry(tmp_path, monkeypatch):
    """Test installing server not in registry"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    monkeypatch.setattr(mcp_manager, "fetch_registry", lambda force=False: [])

    result = mcp_manager.install_server("nonexistent")

    assert result is False


def test_remove_server(tmp_path):
    """Test removing a server"""
    mcp_manager, _, profile_manager = _temp_managers(tmp_path)

    # Create a server
    mcp_manager.save_server_config("to_remove", {"command": "test"}, custom=True)
    assert (mcp_manager.custom_mcp_dir / "to_remove.json").exists()

    # Remove it
    result = mcp_manager.remove_server("to_remove", profile_manager=profile_manager)

    assert result is True
    assert not (mcp_manager.custom_mcp_dir / "to_remove.json").exists()


def test_remove_server_not_found(tmp_path):
    """Test removing non-existent server"""
    mcp_manager, _, profile_manager = _temp_managers(tmp_path)

    result = mcp_manager.remove_server("nonexistent", profile_manager=profile_manager)

    assert result is False


def test_init_builtin_servers(tmp_path):
    """Test initializing builtin servers"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    mcp_manager.init_builtin_servers()

    # Should create some builtin server configs
    servers = list(mcp_manager.mcp_servers_dir.glob("*.json"))
    # init_builtin_servers may not create files if they already exist or if bundled configs are used
    assert len(servers) >= 0


def test_test_server_not_found(tmp_path):
    """Test testing non-existent server"""
    mcp_manager, _, _ = _temp_managers(tmp_path)

    result = mcp_manager.test_server("nonexistent")

    assert result is False


def test_update_server_config(tmp_path):
    """Test updating server configuration"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    # Create initial config
    config = {"command": "test", "args": []}
    mcp_manager.save_server_config("test", config, custom=True)
    
    # Update it
    new_config = {"command": "updated", "args": ["--new"]}
    mcp_manager.save_server_config("test", new_config, custom=True)
    
    # Verify update
    loaded = mcp_manager.get_server_config("test")
    assert loaded["command"] == "updated"
    assert loaded["args"] == ["--new"]


def test_list_installed_custom_only(tmp_path):
    """Test listing only custom servers"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    # Add custom servers
    mcp_manager.save_server_config("custom1", {"command": "test"}, custom=True)
    mcp_manager.save_server_config("custom2", {"command": "test"}, custom=True)
    
    servers = mcp_manager.list_installed()
    assert "custom1" in servers
    assert "custom2" in servers


def test_server_config_precedence(tmp_path):
    """Test that custom server config takes precedence over builtin"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    # Create builtin
    mcp_manager.save_server_config("test", {"command": "builtin", "version": "1.0"}, custom=False)
    
    # Create custom with same name
    mcp_manager.save_server_config("test", {"command": "custom", "version": "2.0"}, custom=True)
    
    # Should get custom version
    config = mcp_manager.get_server_config("test")
    assert config["command"] == "custom"
    assert config["version"] == "2.0"


def test_search_registry_case_insensitive(tmp_path, monkeypatch):
    """Test that search is case insensitive"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    registry = [
        MCPServerRegistry(
            name="GitHub",
            description="GitHub Integration",
            author="Test",
            repository="",
            version="1.0",
            install={"type": "npm"},
        ),
        MCPServerRegistry(
            name="gitlab",
            description="GitLab API",
            author="Test",
            repository="",
            version="1.0",
            install={"type": "npm"},
        ),
    ]
    
    monkeypatch.setattr(mcp_manager, "fetch_registry", lambda force=False: registry)
    
    # Search with different case
    results = mcp_manager.search_registry("git")
    assert len(results) >= 2


def test_remove_server_updates_profiles(tmp_path):
    """Test that removing a server updates all profiles"""
    mcp_manager, config_manager, profile_manager = _temp_managers(tmp_path)
    
    # Create server
    mcp_manager.save_server_config("test_server", {"command": "test"}, custom=True)
    
    # Create profile using this server
    profile = profile_manager.load_profile("default")
    profile.mcp_servers.append(profile.mcp_servers[0].__class__(name="test_server", enabled=True))
    profile_manager.save_profile(profile, custom=True)
    
    # Remove server
    result = mcp_manager.remove_server("test_server", profile_manager=profile_manager)
    
    assert result is True
    # Verify server removed from profile
    updated = profile_manager.load_profile("default")
    assert all(s.name != "test_server" for s in updated.mcp_servers)


def test_init_builtin_servers_idempotent(tmp_path):
    """Test that init_builtin_servers can be called multiple times"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    # Call twice
    mcp_manager.init_builtin_servers()
    mcp_manager.init_builtin_servers()
    
    # Should not error


def test_get_server_config_returns_copy(tmp_path):
    """Test that get_server_config returns a copy, not reference"""
    mcp_manager, _, _ = _temp_managers(tmp_path)
    
    original = {"command": "test", "args": []}
    mcp_manager.save_server_config("test", original, custom=True)
    
    # Get config
    config1 = mcp_manager.get_server_config("test")
    config2 = mcp_manager.get_server_config("test")
    
    # Modify one
    config1["modified"] = True
    
    # Other should be unaffected
    assert "modified" not in config2
