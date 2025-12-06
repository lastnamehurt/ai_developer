from pathlib import Path

from click.testing import CliRunner

from aidev.cli import use, status
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager
from aidev.mcp_config_generator import MCPConfigGenerator


def _temp_managers(tmp_path: Path) -> tuple[ConfigManager, ProfileManager, MCPManager]:
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
    return cm, ProfileManager(), MCPManager()


def test_profile_switch_and_status(tmp_path, monkeypatch):
    cm, pm, mm = _temp_managers(tmp_path)
    cm.init_directories()
    pm.profiles_dir = cm.profiles_dir
    pm.custom_profiles_dir = cm.custom_profiles_dir
    pm.init_builtin_profiles()
    mm.mcp_servers_dir = cm.mcp_servers_dir
    mm.custom_mcp_dir = cm.custom_mcp_dir
    mm.cache_dir = cm.cache_dir

    # Monkeypatch globals in cli
    monkeypatch.setattr("aidev.cli.config_manager", cm)
    monkeypatch.setattr("aidev.cli.profile_manager", pm)
    monkeypatch.setattr("aidev.cli.mcp_manager", mm)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cm.init_project(project_dir=project_dir, profile="web")

    runner = CliRunner()
    res_use = runner.invoke(use, ["qa"], env={"PWD": str(project_dir)})
    assert res_use.exit_code == 0
    assert (project_dir / ".aidev" / "profile").read_text().strip() == "qa"

    res_status = runner.invoke(status, [], env={"PWD": str(project_dir)})
    assert res_status.exit_code == 0
    assert "Active profile" in res_status.output
    assert "qa" in res_status.output
    # Ensure status lists MCP servers from the profile
    assert "filesystem" in res_status.output


def test_mcp_config_generation(tmp_path):
    cm, pm, mm = _temp_managers(tmp_path)
    cm.init_directories()
    pm.profiles_dir = cm.profiles_dir
    pm.custom_profiles_dir = cm.custom_profiles_dir
    pm.init_builtin_profiles()
    mm.mcp_servers_dir = cm.mcp_servers_dir
    mm.custom_mcp_dir = cm.custom_mcp_dir
    mm.cache_dir = cm.cache_dir
    mm.init_builtin_servers()

    generator = MCPConfigGenerator()
    generator.mcp_manager = mm
    generator.config_manager = cm
    profile = pm.load_profile("default")
    config_path = tmp_path / "cursor-mcp.json"
    generator.generate_config("cursor", profile, config_path)
    assert config_path.exists()
    # Validate JSON structure contains mcpServers
    content = config_path.read_text()
    assert "mcpServers" in content
