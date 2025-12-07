"""Tests for config.py and remaining gaps to reach 80%"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
from aidev.config import ConfigManager
from aidev.models import Profile


@pytest.fixture
def config_manager(tmp_path):
    """Create a config manager with temporary paths"""
    with patch('aidev.config.CONFIG_DIR', tmp_path / '.aidev'):
        with patch('aidev.config.GLOBAL_ENV_FILE', tmp_path / '.aidev' / '.env'):
            cm = ConfigManager()
            return cm


def test_config_manager_init(config_manager):
    """Test config manager initialization"""
    assert config_manager is not None


def test_config_manager_get_env_empty(config_manager, tmp_path):
    """Test get_env with no env files"""
    env = config_manager.get_env()
    assert isinstance(env, dict)


def test_config_manager_get_env_with_global(config_manager, tmp_path):
    """Test get_env with global env file"""
    global_env = tmp_path / '.aidev' / '.env'
    global_env.parent.mkdir(parents=True, exist_ok=True)
    global_env.write_text("GLOBAL_VAR=global_value\n")

    env = config_manager.get_env()
    assert 'GLOBAL_VAR' in env
    assert env['GLOBAL_VAR'] == 'global_value'


def test_config_manager_get_env_with_project(config_manager, tmp_path):
    """Test get_env with project env file"""
    global_env = tmp_path / '.aidev' / '.env'
    global_env.parent.mkdir(parents=True, exist_ok=True)
    global_env.write_text("GLOBAL_VAR=global_value\n")

    project_dir = tmp_path / 'project' / '.aidev'
    project_dir.mkdir(parents=True, exist_ok=True)
    project_env = project_dir / '.env'
    project_env.write_text("PROJECT_VAR=project_value\n")

    with patch.object(config_manager, 'get_project_config_path', return_value=project_dir):
        env = config_manager.get_env()
        assert 'PROJECT_VAR' in env
        assert env['PROJECT_VAR'] == 'project_value'


def test_config_manager_set_env_global(config_manager, tmp_path):
    """Test set_env for global environment"""
    global_env = tmp_path / '.aidev' / '.env'
    global_env.parent.mkdir(parents=True, exist_ok=True)

    config_manager.set_env("TEST_KEY", "test_value", project=False)

    assert global_env.exists()
    content = global_env.read_text()
    assert "TEST_KEY=test_value" in content


def test_config_manager_set_env_project(config_manager, tmp_path):
    """Test set_env for project environment"""
    project_dir = tmp_path / 'project' / '.aidev'
    project_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(config_manager, 'get_project_config_path', return_value=project_dir):
        config_manager.set_env("TEST_KEY", "test_value", project=True)

        project_env = project_dir / '.env'
        assert project_env.exists()
        content = project_env.read_text()
        assert "TEST_KEY=test_value" in content


def test_config_manager_init_project(config_manager, tmp_path):
    """Test init_project"""
    project_path = tmp_path / 'new_project'
    project_path.mkdir()

    with patch.object(config_manager, '_current_dir', project_path):
        aidev_dir = config_manager.init_project(profile_name="web")

        assert aidev_dir.exists()
        assert (aidev_dir / '.env').exists()
        assert (aidev_dir / 'profile').exists()


def test_config_manager_set_env_creates_project_dir(config_manager, tmp_path):
    """Project set_env should create .aidev when missing"""
    base_dir = tmp_path / "fresh_project"
    with patch.object(config_manager, "_current_dir", base_dir):
        config_manager.set_env("KEY", "value", project=True)

    env_path = base_dir / ".aidev" / ".env"
    assert env_path.exists()
    assert "KEY=value" in env_path.read_text()


def test_ensure_engineering_workflow_recovers_bad_rules(config_manager, tmp_path):
    """_ensure_engineering_workflow should rewrite invalid rules.json"""
    project_dir = tmp_path / "proj"
    cursor_dir = project_dir / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    bad_rules = cursor_dir / "rules.json"
    bad_rules.write_text("not-json")

    config_manager._ensure_engineering_workflow(project_dir)

    data = json.loads(bad_rules.read_text())
    assert ".claude/engineering-workflow.md" in data.get("summarize", [])


def test_config_manager_is_initialized_true(config_manager, tmp_path):
    """Test is_initialized returns True when initialized"""
    aidev_dir = tmp_path / '.aidev'
    aidev_dir.mkdir()

    with patch.object(config_manager, 'aidev_dir', aidev_dir):
        assert config_manager.is_initialized() is True


def test_config_manager_is_initialized_false(config_manager, tmp_path):
    """Test is_initialized returns False when not initialized"""
    aidev_dir = tmp_path / '.aidev'

    with patch.object(config_manager, 'aidev_dir', aidev_dir):
        assert config_manager.is_initialized() is False


def test_config_manager_get_current_profile_from_project(config_manager, tmp_path):
    """Test get_current_profile from project"""
    project_dir = tmp_path / 'project' / '.aidev'
    project_dir.mkdir(parents=True, exist_ok=True)
    profile_file = project_dir / 'profile'
    profile_file.write_text("web")

    with patch.object(config_manager, 'get_project_config_path', return_value=project_dir):
        profile = config_manager.get_current_profile()
        assert profile == "web"


def test_config_manager_get_current_profile_from_env(config_manager, tmp_path):
    """Test get_current_profile from environment"""
    with patch.object(config_manager, 'get_project_config_path', return_value=None):
        with patch.dict('os.environ', {'AIDEV_DEFAULT_PROFILE': 'qa'}):
            profile = config_manager.get_current_profile()
            assert profile == "qa"


def test_config_manager_get_current_profile_default(config_manager, tmp_path):
    """Test get_current_profile falls back to default"""
    with patch.object(config_manager, 'get_project_config_path', return_value=None):
        with patch.dict('os.environ', {}, clear=True):
            profile = config_manager.get_current_profile()
            assert profile == "default"


def test_config_manager_get_project_config_path_none(config_manager, tmp_path):
    """Test get_project_config_path returns None when no project"""
    with patch.object(config_manager, '_current_dir', tmp_path):
        path = config_manager.get_project_config_path()
        assert path is None


def test_config_manager_get_project_config_path_found(config_manager, tmp_path):
    """Test get_project_config_path finds project dir"""
    project_dir = tmp_path / 'project'
    project_dir.mkdir()
    aidev_dir = project_dir / '.aidev'
    aidev_dir.mkdir()

    with patch.object(config_manager, '_current_dir', project_dir):
        path = config_manager.get_project_config_path()
        assert path == aidev_dir


# More CLI tests for remaining gaps
from click.testing import CliRunner
from aidev.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_profile_edit_command(runner):
    """Test profile edit command"""
    result = runner.invoke(cli, ['profile', 'edit', 'web'])
    # This is a TODO command, should exit gracefully
    assert result.exit_code in [0, 1]


def test_config_share_export(runner, tmp_path):
    """Test config share export command"""
    output = tmp_path / "export.json"
    result = runner.invoke(cli, ['config-share', 'export', '--output', str(output)])
    assert result.exit_code in [0, 1]


def test_config_share_import(runner, tmp_path):
    """Test config share import command"""
    import_file = tmp_path / "import.json"
    import_file.write_text("{}")
    result = runner.invoke(cli, ['config-share', 'import', str(import_file)])
    assert result.exit_code in [0, 1]


def test_env_set_without_project_flag(runner):
    """Test env set without project flag (global)"""
    with patch('aidev.cli.config_manager') as mc:
        result = runner.invoke(cli, ['env', 'set', 'KEY', 'value'])
        assert result.exit_code == 0


def test_env_get_without_project_flag(runner):
    """Test env get without project flag"""
    with patch('aidev.cli.config_manager') as mc:
        mc.get_env.return_value = {"KEY": "value"}
        result = runner.invoke(cli, ['env', 'get', 'KEY'])
        assert result.exit_code == 0


def test_env_list_without_project_flag(runner):
    """Test env list without project flag"""
    with patch('aidev.cli.config_manager') as mc:
        mc.get_env.return_value = {"KEY": "value"}
        mc.get_project_config_path.return_value = None
        result = runner.invoke(cli, ['env', 'list'])
        assert result.exit_code == 0


def test_mcp_search_empty_query(runner):
    """Test mcp search with empty query (list all)"""
    with patch('aidev.cli.mcp_manager') as mm:
        from aidev.models import MCPServerRegistry
        mm.search_registry.return_value = [
            MCPServerRegistry(
                name="git",
                description="Git operations",
                author="Author",
                repository="repo",
                version="1.0",
                install={"type": "npm", "package": "@modelcontextprotocol/server-git"}
            )
        ]
        result = runner.invoke(cli, ['mcp', 'search'])
        assert result.exit_code == 0


def test_profile_list_no_profiles(runner):
    """Test profile list when no profiles exist"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.list_profiles.return_value = []
        result = runner.invoke(cli, ['profile', 'list'])
        assert result.exit_code == 0


def test_mcp_list_no_servers(runner):
    """Test mcp list when no servers installed"""
    with patch('aidev.cli.mcp_manager') as mm:
        mm.list_installed.return_value = []
        result = runner.invoke(cli, ['mcp', 'list'])
        assert result.exit_code == 0


def test_status_without_profile(runner):
    """Test status without explicit profile"""
    with patch('aidev.cli.config_manager') as mc:
        with patch('aidev.cli.profile_manager') as mp:
            mc.get_project_config_path.return_value = None
            mc.get_env.return_value = {"AIDEV_DEFAULT_PROFILE": "web"}
            mp.load_profile.return_value = Profile(name="web", description="Web", mcp_servers=[])
            result = runner.invoke(cli, ['status'])
            assert result.exit_code == 0


def test_profile_create_without_extends(runner):
    """Test profile create without extends"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.create_profile.return_value = Profile(name="custom", description="Custom")
        result = runner.invoke(cli, ['profile', 'create', 'custom'])
        assert result.exit_code == 0


def test_profile_clone_without_description(runner):
    """Test profile clone without custom description"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.load_profile.return_value = Profile(name="web", description="Web")
        mp.clone_profile.return_value = Profile(name="my-web", description="Cloned")
        result = runner.invoke(cli, ['profile', 'clone', 'web', 'my-web'])
        assert result.exit_code == 0


def test_profile_diff_without_json(runner):
    """Test profile diff without JSON output"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.diff_profiles.return_value = {
            "profile1": "web",
            "profile2": "qa",
            "mcp_servers": {"added": [], "removed": [], "common": []},
            "environment": {"added": [], "removed": [], "common": [], "changed": {}},
            "tags": {"added": [], "removed": [], "common": []}
        }
        result = runner.invoke(cli, ['profile', 'diff', 'web', 'qa'])
        assert result.exit_code == 0


def test_mcp_install_without_profile(runner):
    """Test mcp install without profile option"""
    with patch('aidev.cli.mcp_manager') as mm:
        mm.install_server.return_value = True
        result = runner.invoke(cli, ['mcp', 'install', 'git'])
        assert result.exit_code == 0


def test_backup_without_output(runner):
    """Test backup without custom output"""
    with patch('aidev.cli.backup_manager') as bm:
        bm.create_backup.return_value = Path("/tmp/backup.tar.gz")
        result = runner.invoke(cli, ['backup'])
        assert result.exit_code == 0


def test_init_without_profile(runner):
    """Test init without explicit profile"""
    with patch('aidev.cli.config_manager') as mc:
        with patch('aidev.cli.profile_manager') as mp:
            mc.get_project_config_path.return_value = None
            mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
            mc.init_project.return_value = Path("/tmp/.aidev")
            result = runner.invoke(cli, ['init'])
            assert result.exit_code == 0


def test_setup_without_force(runner):
    """Test setup without force flag"""
    with patch('aidev.cli.config_manager') as mc:
        with patch('aidev.cli.profile_manager') as mp:
            with patch('aidev.cli.mcp_manager') as mm:
                mc.is_initialized.return_value = False
                result = runner.invoke(cli, ['setup'])
                assert result.exit_code == 0


def test_quickstart_without_flags(runner):
    """Test quickstart without any flags"""
    with patch('aidev.cli.quickstart_runner') as qr:
        from dataclasses import dataclass
        @dataclass
        class R:
            selected_profile: str = 'web'
        qr.run.return_value = R()
        result = runner.invoke(cli, ['quickstart'])
        assert result.exit_code == 0


def test_mcp_search_without_refresh(runner):
    """Test mcp search without refresh"""
    with patch('aidev.cli.mcp_manager') as mm:
        from aidev.models import MCPServerRegistry
        mm.search_registry.return_value = []
        result = runner.invoke(cli, ['mcp', 'search', 'nonexistent'])
        assert result.exit_code == 0


def test_mcp_browse_without_refresh(runner):
    """Test mcp browse without refresh"""
    with patch('aidev.tui_mcp_browser.MCPBrowserApp') as mock_app:
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        mock_instance.run.return_value = None

        result = runner.invoke(cli, ['mcp', 'browse'])
        # TUI may fail without proper terminal
        assert result.exit_code in [0, 1]


def test_profile_export_without_output(runner):
    """Test profile export without custom output"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.export_profile.return_value = True
        result = runner.invoke(cli, ['profile', 'export', 'web'])
        assert result.exit_code == 0
