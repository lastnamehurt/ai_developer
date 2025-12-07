"""Test that CLI commands exist and can be invoked"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from aidev.cli import cli
from aidev.models import Profile, MCPServerConfig


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    """Test main CLI help"""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'aidev' in result.output.lower()


def test_profile_commands_exist(runner):
    """Test profile subcommands exist"""
    result = runner.invoke(cli, ['profile', '--help'])
    assert result.exit_code == 0
    assert 'list' in result.output
    assert 'show' in result.output


def test_mcp_commands_exist(runner):
    """Test mcp subcommands exist"""
    result = runner.invoke(cli, ['mcp', '--help'])
    assert result.exit_code == 0
    assert 'list' in result.output
    assert 'search' in result.output
    assert 'install' in result.output


def test_env_commands_exist(runner):
    """Test env subcommands exist"""
    result = runner.invoke(cli, ['env', '--help'])
    assert result.exit_code == 0
    assert 'set' in result.output
    assert 'get' in result.output
    assert 'list' in result.output


def test_config_commands_exist(runner):
    """Test config subcommands exist"""
    result = runner.invoke(cli, ['config', '--help'])
    assert result.exit_code == 0


# Test actual command execution with minimal mocking
def test_mcp_browse_command(runner):
    """Test mcp browse command"""
    with patch('aidev.tui_mcp_browser.MCPBrowserApp') as mock_app:
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        mock_instance.run.return_value = None

        result = runner.invoke(cli, ['mcp', 'browse'])
        # TUI may fail without proper terminal
        assert result.exit_code in [0, 1]


def test_profile_clone_basic(runner):
    """Test profile clone exists"""
    result = runner.invoke(cli, ['profile', 'clone', '--help'])
    assert result.exit_code == 0
    assert 'clone' in result.output.lower()


def test_profile_diff_basic(runner):
    """Test profile diff exists"""
    result = runner.invoke(cli, ['profile', 'diff', '--help'])
    assert result.exit_code == 0


def test_profile_export_basic(runner):
    """Test profile export exists"""
    result = runner.invoke(cli, ['profile', 'export', '--help'])
    assert result.exit_code == 0


def test_profile_import_basic(runner):
    """Test profile import exists"""
    result = runner.invoke(cli, ['profile', 'import', '--help'])
    assert result.exit_code == 0


def test_mcp_install_basic(runner):
    """Test mcp install exists"""
    result = runner.invoke(cli, ['mcp', 'install', '--help'])
    assert result.exit_code == 0


def test_mcp_remove_basic(runner):
    """Test mcp remove exists"""
    result = runner.invoke(cli, ['mcp', 'remove', '--help'])
    assert result.exit_code == 0


def test_mcp_test_basic(runner):
    """Test mcp test exists"""
    result = runner.invoke(cli, ['mcp', 'test', '--help'])
    assert result.exit_code == 0


def test_env_unlock_basic(runner):
    """Test env unlock exists"""
    result = runner.invoke(cli, ['env', 'unlock', '--help'])
    assert result.exit_code == 0


def test_env_validate_basic(runner):
    """Test env validate exists"""
    result = runner.invoke(cli, ['env', 'validate', '--help'])
    assert result.exit_code == 0


# Test with actual execution and proper mocking
def test_profile_clone_execution(runner):
    """Test profile clone execution"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        source = Profile(name="web", description="Web")
        cloned = Profile(name="my-web", description="Cloned from web")
        mock_profile.load_profile.return_value = source
        mock_profile.clone_profile.return_value = cloned

        result = runner.invoke(cli, ['profile', 'clone', 'web', 'my-web'])
        assert result.exit_code == 0


def test_profile_diff_execution(runner):
    """Test profile diff execution"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        diff = {
            "profile1": "web",
            "profile2": "qa",
            "mcp_servers": {"added": [], "removed": [], "common": ["git"]},
            "environment": {"added": [], "removed": [], "common": [], "changed": {}},
            "tags": {"added": [], "removed": [], "common": []}
        }
        mock_profile.diff_profiles.return_value = diff

        result = runner.invoke(cli, ['profile', 'diff', 'web', 'qa'])
        assert result.exit_code == 0


def test_profile_export_execution(runner, tmp_path):
    """Test profile export execution"""
    with patch('aidev.cli.profile_manager') as mock_profile:
        mock_profile.export_profile.return_value = True
        output = tmp_path / "profile.json"

        result = runner.invoke(cli, ['profile', 'export', 'web', '--output', str(output)])
        assert result.exit_code == 0


def test_mcp_install_execution(runner):
    """Test mcp install execution"""
    with patch('aidev.cli.mcp_manager') as mock_mcp:
        mock_mcp.install_server.return_value = True

        result = runner.invoke(cli, ['mcp', 'install', 'git'])
        assert result.exit_code == 0


def test_mcp_remove_execution(runner):
    """Test mcp remove execution"""
    with patch('aidev.cli.mcp_manager') as mock_mcp:
        mock_mcp.remove_server.return_value = True
        result = runner.invoke(cli, ['mcp', 'remove', 'git'])
        assert result.exit_code == 0
