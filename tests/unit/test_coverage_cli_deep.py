"""Deep CLI coverage tests targeting uncovered code paths"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from aidev.cli import cli
from aidev.models import Profile, MCPServerConfig


@pytest.fixture
def runner():
    return CliRunner()


# Test tool launch commands with profile handling
def test_cursor_with_explicit_profile(runner):
    """Test cursor command with explicit profile"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                mp.load_profile.return_value = Profile(name="web", description="Web", mcp_servers=[])
                mt.get_tool_config_path.return_value = Path("/tmp/cursor.json")
                mt.launch_tool.return_value = None

                result = runner.invoke(cli, ['cursor', '--profile', 'web'])
                assert result.exit_code == 0
                mp.load_profile.assert_called_once_with('web')


def test_cursor_with_project_profile(runner, tmp_path):
    """Test cursor command using project profile file"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    project_dir = tmp_path / ".aidev"
                    project_dir.mkdir()
                    profile_file = project_dir / "profile"
                    profile_file.write_text("qa")

                    mc.get_project_config_path.return_value = project_dir
                    mp.load_profile.return_value = Profile(name="qa", description="QA", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/cursor.json")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['cursor'])
                    assert result.exit_code == 0
                    mp.load_profile.assert_called_once_with('qa')


def test_cursor_with_default_profile(runner):
    """Test cursor command falling back to default profile"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    mc.get_project_config_path.return_value = None
                    mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/cursor.json")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['cursor'])
                    assert result.exit_code == 0
                    mp.load_profile.assert_called_once_with('default')


def test_cursor_profile_not_found(runner):
    """Test cursor command when profile doesn't exist"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.config_manager') as mc:
            mc.get_project_config_path.return_value = None
            mp.load_profile.return_value = None

            result = runner.invoke(cli, ['cursor', '--profile', 'nonexistent'])
            assert result.exit_code == 0  # Exits gracefully


def test_cursor_with_args(runner):
    """Test cursor command with additional arguments"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    mc.get_project_config_path.return_value = None
                    mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/cursor.json")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['cursor', '/path/to/project'])
                    assert result.exit_code == 0
                    # Verify launch_tool was called with args
                    mt.launch_tool.assert_called_once()


def test_claude_command(runner):
    """Test claude command"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    mc.get_project_config_path.return_value = None
                    mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/claude.json")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['claude'])
                    assert result.exit_code == 0


def test_codex_command(runner):
    """Test codex command"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    mc.get_project_config_path.return_value = None
                    mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/codex.toml")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['codex'])
                    assert result.exit_code == 0


def test_gemini_command(runner):
    """Test gemini command"""
    with patch('aidev.cli.profile_manager') as mp:
        with patch('aidev.cli.tool_manager') as mt:
            with patch('aidev.cli.mcp_config_generator') as mg:
                with patch('aidev.cli.config_manager') as mc:
                    mc.get_project_config_path.return_value = None
                    mp.load_profile.return_value = Profile(name="default", description="Default", mcp_servers=[])
                    mt.get_tool_config_path.return_value = Path("/tmp/gemini.json")
                    mt.launch_tool.return_value = None

                    result = runner.invoke(cli, ['gemini'])
                    assert result.exit_code == 0


# Test profile commands
def test_profile_create(runner, tmp_path):
    """Test profile create command"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.create_profile.return_value = Profile(name="custom", description="Custom profile")
        result = runner.invoke(cli, ['profile', 'create', 'custom'])
        assert result.exit_code == 0


# Test config commands
def test_config_get(runner):
    """Test config get command"""
    with patch('aidev.cli.config_manager') as mc:
        mc.get_config.return_value = {"key": "value"}
        result = runner.invoke(cli, ['config', 'get', 'key'])
        assert result.exit_code == 0


def test_config_set(runner):
    """Test config set command"""
    with patch('aidev.cli.config_manager') as mc:
        mc.set_config.return_value = True
        result = runner.invoke(cli, ['config', 'set', 'key', 'value'])
        assert result.exit_code == 0


def test_config_list(runner):
    """Test config list command"""
    with patch('aidev.cli.config_manager') as mc:
        mc.get_all_config.return_value = {"key1": "val1", "key2": "val2"}
        result = runner.invoke(cli, ['config', 'list'])
        assert result.exit_code == 0


# Test profile list with details
def test_profile_list_with_profiles(runner):
    """Test profile list when profiles exist"""
    with patch('aidev.cli.profile_manager') as mp:
        mp.list_profiles.return_value = ['web', 'qa', 'infra']
        mp.load_profile.side_effect = [
            Profile(name="web", description="Web development"),
            Profile(name="qa", description="QA testing"),
            Profile(name="infra", description="Infrastructure"),
        ]
        result = runner.invoke(cli, ['profile', 'list'])
        assert result.exit_code == 0


# Test mcp list with servers
def test_mcp_list_with_servers(runner):
    """Test mcp list when servers are installed"""
    with patch('aidev.cli.mcp_manager') as mm:
        mm.list_installed.return_value = ['git', 'github', 'filesystem']
        result = runner.invoke(cli, ['mcp', 'list'])
        assert result.exit_code == 0


# Test mcp search with results
def test_mcp_search_with_results(runner):
    """Test mcp search with multiple results"""
    with patch('aidev.cli.mcp_manager') as mm:
        from aidev.models import MCPServerRegistry
        mm.search_registry.return_value = [
            MCPServerRegistry(
                name="git",
                description="Git operations",
                author="Author1",
                repository="repo1",
                version="1.0",
                install={"type": "npm", "package": "@modelcontextprotocol/server-git"}
            ),
            MCPServerRegistry(
                name="github",
                description="GitHub API",
                author="Author2",
                repository="repo2",
                version="1.0",
                install={"type": "npm", "package": "@modelcontextprotocol/server-github"}
            ),
        ]
        result = runner.invoke(cli, ['mcp', 'search', 'git'])
        assert result.exit_code == 0
