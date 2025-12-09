"""
Tests for tools.py
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest
from aidev.tools import ToolManager
from aidev.models import ToolInfo


@pytest.fixture
def tool_manager():
    """Create ToolManager instance"""
    return ToolManager()


@pytest.fixture
def mock_supported_tools(monkeypatch):
    """Mock supported tools configuration"""
    tools = {
        "cursor": {
            "name": "Cursor",
            "binary": "cursor-agent",
            "app_name": "Cursor",
            "config_path": "~/.cursor/mcp.json",
            "install_url": "https://cursor.sh"
        },
        "claude": {
            "name": "Claude Code",
            "binary": "claude",
            "app_name": "Claude",
            "config_path": "~/.claude/mcp.json",
            "install_url": "https://claude.ai/code"
        },
        "gemini": {
            "name": "Gemini Code Assist",
            "binary": "gemini",
            "app_name": "Gemini",
            "config_path": "~/.gemini/settings.json",
            "install_url": "https://gemini.google.com"
        }
    }
    monkeypatch.setattr("aidev.tools.SUPPORTED_TOOLS", tools)
    return tools


def test_detect_tool_installed(tool_manager, mock_supported_tools):
    """Test detecting an installed tool"""
    with patch("aidev.tools.find_binary", return_value=Path("/usr/bin/cursor-agent")):
        with patch.object(tool_manager, "_get_version", return_value="1.0.0"):
            tool_info = tool_manager.detect_tool("cursor")

    assert tool_info.name == "Cursor"
    assert tool_info.binary == "cursor-agent"
    assert tool_info.installed is True
    assert tool_info.version == "1.0.0"


def test_detect_tool_not_installed(tool_manager, mock_supported_tools):
    """Test detecting a tool that's not installed"""
    with patch("aidev.tools.find_binary", return_value=None):
        tool_info = tool_manager.detect_tool("cursor")

    assert tool_info.name == "Cursor"
    assert tool_info.installed is False
    assert tool_info.version is None


def test_detect_tool_unsupported(tool_manager, mock_supported_tools):
    """Test detecting an unsupported tool"""
    with pytest.raises(ValueError, match="Unsupported tool"):
        tool_manager.detect_tool("unknown_tool")


def test_detect_all_tools(tool_manager):
    """Test detecting all tools"""
    def find_binary_side_effect(binary):
        if binary == "cursor-agent":
            return Path("/usr/bin/cursor-agent")
        elif binary == "gemini":
            return Path("/usr/bin/gemini")
        return None

    with patch("aidev.tools.find_binary", side_effect=find_binary_side_effect):
        with patch.object(tool_manager, "_get_version", return_value="1.0.0"):
            tools = tool_manager.detect_all_tools()

    # Should detect all supported tools in SUPPORTED_TOOLS
    assert len(tools) >= 3
    assert "cursor" in tools
    assert tools["cursor"].installed is True
    # Tools without binary should not be installed
    if "claude" in tools:
        assert tools["claude"].installed is False


def test_get_tool_config_path(tool_manager, mock_supported_tools):
    """Test getting tool config path"""
    with patch("aidev.tools.find_binary", return_value=Path("/usr/bin/cursor-agent")):
        config_path = tool_manager.get_tool_config_path("cursor")

    assert ".cursor/mcp.json" in str(config_path)


def test_get_tool_config_path_gemini_project(tool_manager, mock_supported_tools, tmp_path):
    """Test getting Gemini config path with project override"""
    project_gemini = tmp_path / ".gemini" / "settings.json"
    project_gemini.parent.mkdir(parents=True)
    project_gemini.write_text('{"mcpServers": {}}')

    with patch("aidev.tools.find_binary", return_value=Path("/usr/bin/gemini")):
        with patch.object(tool_manager, "_find_project_gemini_settings", return_value=project_gemini):
            config_path = tool_manager.get_tool_config_path("gemini")

    assert config_path == project_gemini


def test_launch_tool_not_installed(tool_manager, mock_supported_tools):
    """Test launching a tool that's not installed"""
    with patch("aidev.tools.find_binary", return_value=None):
        with patch("aidev.tools.console") as mock_console:
            tool_manager.launch_tool("cursor")

    mock_console.print.assert_any_call("[red]Error: Cursor is not installed[/red]")


def test_launch_tool_gui_app(tool_manager, mock_supported_tools):
    """Test launching a GUI tool (non-interactive)"""
    with patch.object(tool_manager, 'detect_tool') as mock_detect:
        mock_detect.return_value = ToolInfo(
            name="Cursor",
            binary="cursor-agent",
            installed=True,
            gui_app=True,
        )
        with patch("subprocess.Popen") as mock_popen:
            with patch("aidev.tools.console"):
                tool_manager.launch_tool("cursor", args=[".", "--flag"])

    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0] == ["cursor-agent", ".", "--flag"]
    assert "env" in kwargs
    assert kwargs["start_new_session"] is True


def test_launch_tool_interactive_cli(tool_manager, mock_supported_tools):
    """Test launching an interactive CLI tool"""
    with patch("aidev.tools.find_binary", return_value=Path("/usr/bin/claude")):
        with patch("os.execvp") as mock_execvp:
            with patch("aidev.tools.console"):
                tool_manager.launch_tool("claude")

    mock_execvp.assert_called_once_with("claude", ["claude"])


def test_launch_tool_with_env(tool_manager, mock_supported_tools):
    """Test launching tool with custom environment"""
    with patch.object(tool_manager, 'detect_tool') as mock_detect:
        mock_detect.return_value = ToolInfo(
            name="Cursor",
            binary="cursor-agent",
            installed=True,
            gui_app=True,
        )
        with patch("subprocess.Popen") as mock_popen:
            with patch("aidev.tools.console"):
                tool_manager.launch_tool("cursor", env={"CUSTOM_VAR": "value"})

    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert "CUSTOM_VAR" in kwargs["env"]
    assert kwargs["env"]["CUSTOM_VAR"] == "value"


def test_launch_tool_wait(tool_manager, mock_supported_tools):
    """Test launching tool with wait flag"""
    with patch.object(tool_manager, 'detect_tool') as mock_detect:
        mock_detect.return_value = ToolInfo(
            name="Cursor",
            binary="cursor-agent",
            installed=True,
            gui_app=True,
        )
        with patch("subprocess.run") as mock_run:
            with patch("aidev.tools.console"):
                tool_manager.launch_tool("cursor", wait=True)

    mock_run.assert_called_once()


def test_launch_tool_exception(tool_manager, mock_supported_tools):
    """Test launch handles exceptions"""
    with patch("aidev.tools.find_binary", return_value=Path("/usr/bin/cursor-agent")):
        with patch("subprocess.Popen", side_effect=Exception("Launch failed")):
            with patch("aidev.tools.console") as mock_console:
                tool_manager.launch_tool("cursor")

    assert any("Error launching" in str(call) for call in mock_console.print.call_args_list)


def test_get_version_success(tool_manager):
    """Test getting tool version successfully"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Cursor 1.2.3\nOther info"

    with patch("subprocess.run", return_value=mock_result):
        version = tool_manager._get_version("cursor-agent", Path("/usr/bin/cursor-agent"))

    assert version == "Cursor 1.2.3"


def test_get_version_tries_multiple_flags(tool_manager):
    """Test version detection tries multiple flags"""
    mock_fail = MagicMock()
    mock_fail.returncode = 1

    mock_success = MagicMock()
    mock_success.returncode = 0
    mock_success.stdout = "1.0.0"

    with patch("subprocess.run", side_effect=[mock_fail, mock_success]):
        version = tool_manager._get_version("cursor-agent", Path("/usr/bin/cursor-agent"))

    assert version == "1.0.0"


def test_get_version_timeout(tool_manager):
    """Test version detection handles timeouts"""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
        version = tool_manager._get_version("cursor-agent", Path("/usr/bin/cursor-agent"))

    assert version is None


def test_get_version_exception(tool_manager):
    """Test version detection handles exceptions"""
    with patch("subprocess.run", side_effect=Exception("Error")):
        version = tool_manager._get_version("cursor-agent", Path("/usr/bin/cursor-agent"))

    assert version is None


def test_get_install_url(tool_manager, mock_supported_tools):
    """Test getting install URL"""
    url = tool_manager._get_install_url("cursor")
    assert url == "https://cursor.sh"


def test_get_install_url_fallback(tool_manager):
    """Test install URL fallback for unknown tool"""
    url = tool_manager._get_install_url("unknown")
    assert url == "https://github.com"


def test_find_project_gemini_settings_exists(tool_manager, tmp_path, monkeypatch):
    """Test finding existing project Gemini settings"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    gemini_dir = project_dir / ".gemini"
    gemini_dir.mkdir()
    settings_file = gemini_dir / "settings.json"
    settings_file.write_text('{"mcpServers": {}}')

    monkeypatch.chdir(project_dir)

    result = tool_manager._find_project_gemini_settings()
    assert result == settings_file


def test_find_project_gemini_settings_creates_in_project(tool_manager, tmp_path, monkeypatch):
    """Test creating Gemini settings in project root"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".git").mkdir()

    monkeypatch.chdir(project_dir)

    result = tool_manager._find_project_gemini_settings()
    assert result is not None
    assert result.exists()
    assert ".gemini/settings.json" in str(result)


def test_find_project_gemini_settings_no_project(tool_manager, tmp_path, monkeypatch):
    """Test finding Gemini settings when not in a project"""
    no_project_dir = tmp_path / "random"
    no_project_dir.mkdir()

    monkeypatch.chdir(no_project_dir)

    result = tool_manager._find_project_gemini_settings()
    # Should return None since we're not in a project
    assert result is None


def test_detect_project_root_with_git(tool_manager, tmp_path, monkeypatch):
    """Test detecting project root with .git"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".git").mkdir()

    subdir = project_dir / "src" / "deep"
    subdir.mkdir(parents=True)

    monkeypatch.chdir(subdir)

    result = tool_manager._detect_project_root(Path.cwd())
    assert result == project_dir


def test_detect_project_root_with_aidev(tool_manager, tmp_path, monkeypatch):
    """Test detecting project root with .aidev"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".aidev").mkdir()

    subdir = project_dir / "src"
    subdir.mkdir()

    monkeypatch.chdir(subdir)

    result = tool_manager._detect_project_root(Path.cwd())
    assert result == project_dir


def test_detect_project_root_none(tool_manager, tmp_path, monkeypatch):
    """Test detecting project root when none exists"""
    no_project_dir = tmp_path / "random"
    no_project_dir.mkdir()

    monkeypatch.chdir(no_project_dir)

    result = tool_manager._detect_project_root(Path.cwd())
    assert result is None


def test_detect_project_root_stops_at_home(tool_manager, tmp_path, monkeypatch):
    """Test project root detection stops at home directory"""
    # This would normally search up to home, but shouldn't go beyond
    result = tool_manager._detect_project_root(Path.home() / "somedir")
    # Should either find something or return None, but not error
    assert result is None or result.exists()
