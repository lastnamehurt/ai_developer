from pathlib import Path

from click.testing import CliRunner

from aidev.cli import env_list, env_get, env_validate
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager
from aidev.models import Profile, MCPServerConfig


def _setup_config(tmp_path: Path) -> ConfigManager:
    cm = ConfigManager()
    cm.aidev_dir = tmp_path / ".aidev"
    cm.config_dir = cm.aidev_dir / "config"
    cm.env_file = cm.aidev_dir / ".env"
    cm.profiles_dir = cm.config_dir / "profiles"
    cm.custom_profiles_dir = cm.profiles_dir / "custom"
    cm.mcp_servers_dir = cm.config_dir / "mcp-servers"
    cm.custom_mcp_dir = cm.mcp_servers_dir / "custom"
    cm.memory_banks_dir = cm.aidev_dir / "memory-banks"
    cm.plugins_dir = cm.aidev_dir / "plugins"
    cm.cache_dir = cm.aidev_dir / "cache"
    cm.logs_dir = cm.aidev_dir / "logs"
    cm.tools_config = cm.config_dir / "tools.json"
    cm.init_directories()
    return cm


def test_env_list_masks_and_scopes(tmp_path, monkeypatch):
    cm = _setup_config(tmp_path)
    cm.set_env("GLOBAL_TOKEN", "secret")

    project_dir = tmp_path / "proj"
    (project_dir / ".aidev").mkdir(parents=True, exist_ok=True)
    (project_dir / ".aidev" / ".env").write_text('PROJECT_KEY="value"\n')

    # Inject config_manager into cli module
    monkeypatch.setattr("aidev.cli.config_manager", cm)
    runner = CliRunner()
    with runner.isolated_filesystem():
        # move into project dir to ensure Path.cwd() resolves correctly
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        result = runner.invoke(env_list, ["--project"], env={"PWD": str(project_dir)})
    assert result.exit_code == 0
    assert "***" in result.output
    assert "project" in result.output
    assert "global" in result.output


def test_env_get_and_validate(tmp_path, monkeypatch):
    cm = _setup_config(tmp_path)
    cm.set_env("REQUIRED", "1")

    pm = ProfileManager()
    pm.profiles_dir = cm.profiles_dir
    pm.custom_profiles_dir = cm.custom_profiles_dir
    profile = Profile(
        name="test",
        description="t",
        mcp_servers=[MCPServerConfig(name="filesystem")],
        environment={"REQUIRED": ""},
    )
    pm.save_profile(profile)

    monkeypatch.setattr("aidev.cli.config_manager", cm)
    monkeypatch.setattr("aidev.cli.profile_manager", pm)

    runner = CliRunner()
    res_get = runner.invoke(env_get, ["REQUIRED"])
    assert "REQUIRED=1" in res_get.output

    res_validate = runner.invoke(env_validate, ["--profile", "test"])
    assert "All required env keys are set" in res_validate.output
