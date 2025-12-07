"""
Comprehensive tests for MCP config generator
"""
import json
import toml
from pathlib import Path
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.models import Profile, MCPServerConfig


class StubMCPManager:
    """Stub MCP manager for testing"""
    def get_server_config(self, name: str):
        return {
            "command": "test-server",
            "args": ["--port", "9000"],
            "env": {"API_KEY": "${API_KEY:-default}"},
        }


class StubConfigManager:
    """Stub config manager for testing"""
    def get_env(self):
        return {"API_KEY": "test-key-123"}


def test_generate_cursor_config(tmp_path):
    """Test generating Cursor JSON config"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test profile",
        mcp_servers=[MCPServerConfig(name="test-server", enabled=True)],
    )

    config_path = tmp_path / "cursor_config.json"
    generator.generate_config("cursor", profile, config_path)

    assert config_path.exists()
    data = json.loads(config_path.read_text())
    
    assert "mcpServers" in data
    assert "test-server" in data["mcpServers"]
    server = data["mcpServers"]["test-server"]
    assert server["command"] == "test-server"
    assert server["args"] == ["--port", "9000"]
    assert "API_KEY" in server["env"]


def test_generate_claude_config(tmp_path):
    """Test generating Claude JSON config"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="server1", enabled=True)],
    )

    config_path = tmp_path / "claude_config.json"
    generator.generate_config("claude", profile, config_path)

    assert config_path.exists()
    data = json.loads(config_path.read_text())
    
    assert "mcpServers" in data
    assert "server1" in data["mcpServers"]


def test_generate_codex_config(tmp_path):
    """Test generating Codex TOML config"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="git", enabled=True)],
    )

    config_path = tmp_path / "config.toml"
    generator.generate_config("codex", profile, config_path)

    assert config_path.exists()
    data = toml.load(config_path)
    
    assert "mcp_servers" in data
    assert "git" in data["mcp_servers"]
    assert data["features"]["rmcp_client"] is True


def test_generate_zed_config(tmp_path):
    """Test generating Zed JSON config"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="filesystem", enabled=True)],
    )

    config_path = tmp_path / "zed_settings.json"
    generator.generate_config("zed", profile, config_path)

    assert config_path.exists()
    data = json.loads(config_path.read_text())

    # Zed uses same format as other tools
    assert "mcpServers" in data
    assert "filesystem" in data["mcpServers"]


def test_generate_gemini_config(tmp_path):
    """Test generating Gemini JSON config"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="github", enabled=True)],
    )

    config_path = tmp_path / "gemini.json"
    generator.generate_config("gemini", profile, config_path)

    assert config_path.exists()
    data = json.loads(config_path.read_text())
    
    assert "mcpServers" in data
    assert "github" in data["mcpServers"]


def test_generate_config_disabled_server(tmp_path):
    """Test that disabled servers are not included"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[
            MCPServerConfig(name="enabled-server", enabled=True),
            MCPServerConfig(name="disabled-server", enabled=False),
        ],
    )

    config_path = tmp_path / "config.json"
    generator.generate_config("cursor", profile, config_path)

    data = json.loads(config_path.read_text())
    
    assert "enabled-server" in data["mcpServers"]
    assert "disabled-server" not in data["mcpServers"]


def test_generate_config_empty_profile(tmp_path):
    """Test generating config with empty profile"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="empty",
        description="Empty profile",
        mcp_servers=[],
    )

    config_path = tmp_path / "config.json"
    generator.generate_config("cursor", profile, config_path)

    data = json.loads(config_path.read_text())
    
    # Should still create valid config, just with empty servers
    assert "mcpServers" in data
    assert len(data["mcpServers"]) == 0


def test_generate_config_missing_server_config(tmp_path):
    """Test handling of missing server config"""
    generator = MCPConfigGenerator()
    
    class MissingMCPManager:
        def get_server_config(self, name: str):
            return None  # Server not found
    
    generator.mcp_manager = MissingMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="nonexistent", enabled=True)],
    )

    config_path = tmp_path / "config.json"
    generator.generate_config("cursor", profile, config_path)

    # Should skip missing servers
    data = json.loads(config_path.read_text())
    assert len(data["mcpServers"]) == 0


def test_env_expansion(tmp_path):
    """Test environment variable expansion"""
    generator = MCPConfigGenerator()
    
    class EnvMCPManager:
        def get_server_config(self, name: str):
            return {
                "command": "server",
                "args": [],
                "env": {
                    "VAR1": "${VAR1}",
                    "VAR2": "${VAR2}",
                    "LITERAL": "no-expansion",
                },
            }
    
    class EnvConfigManager:
        def get_env(self):
            return {"VAR1": "expanded-value", "VAR2": "another-value"}
    
    generator.mcp_manager = EnvMCPManager()
    generator.config_manager = EnvConfigManager()

    profile = Profile(
        name="test",
        description="Test",
        mcp_servers=[MCPServerConfig(name="test", enabled=True)],
    )

    config_path = tmp_path / "config.json"
    generator.generate_config("cursor", profile, config_path)

    data = json.loads(config_path.read_text())
    env = data["mcpServers"]["test"]["env"]
    
    assert env["VAR1"] == "expanded-value"
    assert env["VAR2"] == "another-value"
    assert env["LITERAL"] == "no-expansion"


def test_unsupported_tool(tmp_path):
    """Test handling unsupported tool type"""
    generator = MCPConfigGenerator()
    generator.mcp_manager = StubMCPManager()
    generator.config_manager = StubConfigManager()

    profile = Profile(name="test", description="Test", mcp_servers=[])
    config_path = tmp_path / "config.json"
    
    # Should handle gracefully or raise appropriate error
    try:
        generator.generate_config("unsupported-tool", profile, config_path)
        # If it succeeds, check it created something
        assert config_path.exists()
    except (ValueError, KeyError):
        # Or it might raise an error - both acceptable
        pass
