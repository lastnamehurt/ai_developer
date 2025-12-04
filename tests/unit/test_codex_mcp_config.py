"""
Tests for generating Codex MCP configuration
"""
import toml
from pathlib import Path
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.models import Profile, MCPServerConfig


def test_generate_codex_config(tmp_path):
    """Ensure Codex TOML config is written with MCP servers and rmcp_client enabled."""
    generator = MCPConfigGenerator()

    # Stub MCP manager/env to avoid touching real configs
    class StubMCPManager:
        def get_server_config(self, name: str):
            return {
                "command": "echo",
                "args": ["hello"],
                "env": {"FOO": "${BAR:-baz}"},
            }

    class StubConfigManager:
        def get_env(self):
            return {"BAR": "qux"}

    generator.mcp_manager = StubMCPManager()  # type: ignore
    generator.config_manager = StubConfigManager()  # type: ignore

    profile = Profile(
        name="test",
        description="",
        mcp_servers=[MCPServerConfig(name="stub", enabled=True)],
    )

    config_path = tmp_path / "config.toml"
    generator.generate_config("codex", profile, config_path)

    data = toml.load(config_path)

    assert "mcp_servers" in data
    assert data["mcp_servers"]["stub"]["command"] == "echo"
    # env should be expanded via profile/global env
    assert data["mcp_servers"]["stub"]["env"]["FOO"] == "qux"

    # rmcp_client should be enabled by default
    assert data["features"]["rmcp_client"] is True
