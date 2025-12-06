from pathlib import Path

from aidev.quickstart import QuickstartRunner
from aidev.config import ConfigManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager


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

    pm = ProfileManager()
    pm.profiles_dir = cm.profiles_dir
    pm.custom_profiles_dir = cm.custom_profiles_dir

    mm = MCPManager()
    mm.mcp_servers_dir = cm.mcp_servers_dir
    mm.custom_mcp_dir = cm.custom_mcp_dir
    mm.cache_dir = cm.cache_dir

    return cm, pm, mm


def test_quickstart_js_project(tmp_path):
    # Create sample JS project
    project_dir = tmp_path / "jsproj"
    project_dir.mkdir()
    (project_dir / "package.json").write_text('{"name":"demo"}')
    (project_dir / "tsconfig.json").write_text("{}")

    cm, pm, mm = _temp_managers(tmp_path)
    cm.init_directories()
    pm.init_builtin_profiles()
    mm.init_builtin_servers()

    runner = QuickstartRunner(cm, pm, mm)
    result = runner.run(project_dir=project_dir, auto_confirm=True)

    assert result.selected_profile in pm.list_profiles()
    assert (project_dir / ".aidev" / "config.json").exists()
    assert (project_dir / ".aidev" / "profile").read_text().strip() == result.selected_profile


def test_quickstart_python_project(tmp_path):
    project_dir = tmp_path / "pyproj"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("requests")

    cm, pm, mm = _temp_managers(tmp_path)
    cm.init_directories()
    pm.init_builtin_profiles()
    mm.init_builtin_servers()

    runner = QuickstartRunner(cm, pm, mm)
    result = runner.run(project_dir=project_dir, auto_confirm=True)

    assert result.selected_profile in pm.list_profiles()
    assert (project_dir / ".aidev" / "config.json").exists()
