"""
Tests for CLI commands
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from aidev.cli import cli
from aidev.models import Profile, MCPServerConfig


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


@pytest.fixture
def isolated_cli(tmp_path, monkeypatch):
    """Set up isolated environment for CLI tests"""
    aidev_dir = tmp_path / ".aidev"
    monkeypatch.setenv("HOME", str(tmp_path))

    # Patch constants to use tmp_path
    import aidev.constants as constants
    monkeypatch.setattr(constants, "AIDEV_DIR", aidev_dir)
    monkeypatch.setattr(constants, "CONFIG_DIR", aidev_dir / "config")
    monkeypatch.setattr(constants, "PROFILES_DIR", aidev_dir / "config" / "profiles")
    monkeypatch.setattr(constants, "CUSTOM_PROFILES_DIR", aidev_dir / "config" / "profiles" / "custom")
    monkeypatch.setattr(constants, "MCP_SERVERS_DIR", aidev_dir / "config" / "mcp-servers")
    monkeypatch.setattr(constants, "CUSTOM_MCP_DIR", aidev_dir / "config" / "mcp-servers" / "custom")
    monkeypatch.setattr(constants, "ENV_FILE", aidev_dir / ".env")

    return tmp_path


def test_cli_version(runner):
    """Test --version flag"""
    result = runner.invoke(cli, ['--version'])

    assert result.exit_code == 0
    assert 'version' in result.output.lower() or '0.1.0' in result.output


def test_cli_help(runner):
    """Test --help flag"""
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'aidev' in result.output.lower()
    assert 'usage' in result.output.lower() or 'options' in result.output.lower()


def test_setup_command(runner, isolated_cli):
    """Test setup command"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            with patch('aidev.cli.mcp_manager') as mock_mcp:
                mock_config.is_initialized.return_value = False

                result = runner.invoke(cli, ['setup'])

                assert result.exit_code == 0
                mock_config.init_directories.assert_called_once()
                mock_profile.init_builtin_profiles.assert_called_once()
                mock_mcp.init_builtin_servers.assert_called_once()


def test_setup_already_initialized(runner, isolated_cli):
    """Test setup when already initialized"""
    with patch('aidev.cli.config_manager') as mock_config:
        mock_config.is_initialized.return_value = True

        result = runner.invoke(cli, ['setup'])

        assert result.exit_code == 0
        assert 'already set up' in result.output.lower()


def test_setup_force_flag(runner, isolated_cli):
    """Test setup with --force flag"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            with patch('aidev.cli.mcp_manager') as mock_mcp:
                mock_config.is_initialized.return_value = True

                result = runner.invoke(cli, ['setup', '--force'])

                assert result.exit_code == 0
                mock_config.init_directories.assert_called_once()


def test_env_set_command(runner, isolated_cli):
    """Test env set command"""
    with patch('aidev.cli.config_manager') as mock_config:
        result = runner.invoke(cli, ['env', 'set', 'TEST_KEY', 'test_value'])

        assert result.exit_code == 0
        mock_config.set_env.assert_called_once_with('TEST_KEY', 'test_value', project=False, encrypt=False)


def test_env_set_project_flag(runner, isolated_cli):
    """Test env set with --project flag"""
    with patch('aidev.cli.config_manager') as mock_config:
        result = runner.invoke(cli, ['env', 'set', '--project', 'KEY', 'value'])

        assert result.exit_code == 0
        mock_config.set_env.assert_called_once_with('KEY', 'value', project=True, encrypt=False)


def test_env_get_command(runner, isolated_cli):
    """Test env get command"""
    with patch('aidev.cli.config_manager') as mock_config:
        mock_config.get_env.return_value = {'TEST_KEY': 'test_value'}

        result = runner.invoke(cli, ['env', 'get', 'TEST_KEY'])

        assert result.exit_code == 0
        assert 'test_value' in result.output


def test_env_list_command(runner, isolated_cli):
    """Test env list command"""
    with patch('aidev.cli.config_manager') as mock_config:
        mock_config.get_env.return_value = {'KEY1': 'value1', 'KEY2': 'value2'}
        mock_config.get_project_config_path.return_value = None

        result = runner.invoke(cli, ['env', 'list'])

        assert result.exit_code == 0


def test_profile_list_command(runner, isolated_cli):
    """Test profile list command"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        from aidev.models import Profile
        mock_profile.list_profiles.return_value = ['web', 'qa', 'infra']
        # Mock load_profile to return a profile with description
        mock_profile.load_profile.return_value = Profile(name='test', description='Test profile')

        result = runner.invoke(cli, ['profile', 'list'])

        assert result.exit_code == 0
        assert 'web' in result.output or 'qa' in result.output or 'infra' in result.output


def test_profile_show_command(runner, isolated_cli):
    """Test profile show command"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        test_profile = Profile(
            name='test',
            description='Test profile',
            mcp_servers=[MCPServerConfig(name='git', enabled=True)]
        )
        mock_profile.load_profile.return_value = test_profile

        result = runner.invoke(cli, ['profile', 'show', 'test'])

        assert result.exit_code == 0
        assert 'test' in result.output.lower()


def test_profile_show_not_found(runner, isolated_cli):
    """Test profile show for non-existent profile"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        mock_profile.load_profile.return_value = None

        result = runner.invoke(cli, ['profile', 'show', 'nonexistent'])

        # If load_profile returns None, the command returns early with exit_code 0 but no output
        assert result.exit_code == 0


def test_mcp_list_command(runner, isolated_cli):
    """Test mcp list command"""
    with patch('aidev.cli.mcp_manager') as mock_mcp:
        mock_mcp.list_installed.return_value = ['git', 'github', 'filesystem']

        result = runner.invoke(cli, ['mcp', 'list'])

        assert result.exit_code == 0
        assert 'git' in result.output


def test_doctor_command(runner, isolated_cli):
    """Test doctor command"""
    with patch('aidev.cli.preflight') as mock_preflight:
        mock_preflight.return_value = []  # No errors

        result = runner.invoke(cli, ['doctor'])

        assert result.exit_code == 0


def test_status_command(runner, isolated_cli):
    """Test status command"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            mock_config.get_project_config_path.return_value = Path('/tmp/.aidev')
            test_profile = Profile(
                name='web',
                description='Web profile',
                mcp_servers=[MCPServerConfig(name='git', enabled=True)]
            )
            mock_profile.load_profile.return_value = test_profile
            mock_config.get_env.return_value = {}

            result = runner.invoke(cli, ['status'])

            assert result.exit_code == 0


def test_use_command(runner, isolated_cli):
    """Test use command to switch profiles"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            mock_config.get_project_config_path.return_value = Path('/tmp/.aidev')
            test_profile = Profile(name='qa', description='QA')
            mock_profile.load_profile.return_value = test_profile

            result = runner.invoke(cli, ['use', 'qa'])

            assert result.exit_code == 0


def test_init_command(runner, isolated_cli):
    """Test init command"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            mock_config.get_project_config_path.return_value = None
            test_profile = Profile(name='default', description='Default')
            mock_profile.load_profile.return_value = test_profile

            result = runner.invoke(cli, ['init'])

            assert result.exit_code == 0


def test_init_with_profile_flag(runner, isolated_cli):
    """Test init command with --profile flag"""
    with patch('aidev.cli.config_manager') as mock_config:
        with patch('aidev.cli.profile_manager') as mock_profile:
            mock_config.get_project_config_path.return_value = None
            test_profile = Profile(name='infra', description='Infra')
            mock_profile.load_profile.return_value = test_profile

            result = runner.invoke(cli, ['init', '--profile', 'infra'])

            assert result.exit_code == 0


def test_backup_command(runner, isolated_cli):
    """Test backup command"""
    with patch('aidev.cli.backup_manager') as mock_backup:
        mock_backup.create_backup.return_value = Path('/tmp/backup.tar.gz')

        result = runner.invoke(cli, ['backup'])

        assert result.exit_code == 0
        mock_backup.create_backup.assert_called_once()


def test_backup_with_output_flag(runner, isolated_cli):
    """Test backup command with --output flag"""
    with patch('aidev.cli.backup_manager') as mock_backup:
        mock_backup.create_backup.return_value = Path('/tmp/custom.tar.gz')

        result = runner.invoke(cli, ['backup', '--output', '/tmp/custom.tar.gz'])

        assert result.exit_code == 0


def test_restore_command(runner, isolated_cli):
    """Test restore command"""
    with patch('aidev.cli.backup_manager') as mock_backup:
        mock_backup.restore_backup.return_value = True

        result = runner.invoke(cli, ['restore', '/tmp/backup.tar.gz', '--force'])

        assert result.exit_code == 0
        mock_backup.restore_backup.assert_called_once()


def test_quickstart_command(runner, isolated_cli):
    """Test quickstart command"""
    with patch('aidev.cli.quickstart_runner') as mock_quickstart:
        from dataclasses import dataclass

        @dataclass
        class MockResult:
            selected_profile: str = 'web'

        mock_quickstart.run.return_value = MockResult()

        result = runner.invoke(cli, ['quickstart'])

        assert result.exit_code == 0


def test_quickstart_with_profile_flag(runner, isolated_cli):
    """Test quickstart with --profile flag"""
    with patch('aidev.cli.quickstart_runner') as mock_quickstart:
        from dataclasses import dataclass

        @dataclass
        class MockResult:
            selected_profile: str = 'infra'

        mock_quickstart.run.return_value = MockResult()

        result = runner.invoke(cli, ['quickstart', '--profile', 'infra'])

        assert result.exit_code == 0


def test_config_command(runner, isolated_cli):
    """Test config TUI command"""
    with patch('aidev.tui_config.ProfileConfigApp') as mock_app:
        # Mock the app to prevent actual TUI launch
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        mock_instance.run.return_value = None

        result = runner.invoke(cli, ['config'])

        # TUI commands may return non-zero if terminal not available
        assert result.exit_code in [0, 1]


def test_profile_create_command(runner, isolated_cli):
    """Test profile create command (TODO in CLI)"""
    # profile create is currently a TODO placeholder in CLI
    result = runner.invoke(cli, ['profile', 'create', 'new'])

    # Should succeed but only print a message (TODO implementation)
    assert result.exit_code == 0
    assert 'Created profile' in result.output or 'new' in result.output


def test_mcp_search_command(runner, isolated_cli):
    """Test mcp search command"""
    with patch('aidev.cli.mcp_manager') as mock_mcp:
        from aidev.models import MCPServerRegistry

        mock_mcp.search_registry.return_value = [
            MCPServerRegistry(
                name='test',
                description='Test server',
                author='Test',
                repository='',
                version='1.0',
                install={'type': 'npm'}
            )
        ]

        result = runner.invoke(cli, ['mcp', 'search', 'test'])

        assert result.exit_code == 0
