"""
Tests for generating Gemini MCP configuration
"""
import json
from pathlib import Path
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.models import Profile, MCPServerConfig


def test_generate_gemini_config(tmp_path, monkeypatch):
    """Ensure Gemini settings.json merges mcpServers and preserves other keys."""
    generator = MCPConfigGenerator()

    class StubMCPManager:
        def get_server_config(self, name: str):
            return {
                "command": "echo",
                "args": ["hello"],
                "env": {"FOO": "${BAR:-baz}"},
                "http_url": "https://example.test/stream",
                "http_headers": {"X-Test": "1"},
            }

    class StubConfigManager:
        def get_env(self):
            return {"BAR": "qux"}

    generator.mcp_manager = StubMCPManager()  # type: ignore
    generator.config_manager = StubConfigManager()  # type: ignore

    existing = {
        "ui": {"theme": "Light"},
        "mcpServers": {"old": {"command": "old-cmd"}},
    }
    config_path = tmp_path / "settings.json"
    config_path.write_text(json.dumps(existing))

    profile = Profile(
        name="test",
        description="",
        mcp_servers=[MCPServerConfig(name="stub", enabled=True)],
    )

    generator.generate_config("gemini", profile, config_path)

    data = json.loads(config_path.read_text())
    assert data["ui"]["theme"] == "Light"  # preserved
    assert "old" in data["mcpServers"]  # existing server remains

    stub = data["mcpServers"]["stub"]
    assert stub["command"].endswith("echo")
    assert stub["args"] == ["hello"]
    assert "FOO" in stub["env"]
    assert stub["httpUrl"] == "https://example.test/stream"
    assert stub["headers"]["X-Test"] == "1"
