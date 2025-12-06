import json
from pathlib import Path

from aidev.quickstart import (
    QuickstartDetector,
    QuickstartRunner,
    Recommendation,
    StackDetection,
)
from aidev.config import ConfigManager
from aidev.mcp import MCPManager
from aidev.profiles import ProfileManager


def _temp_managers(tmp_path: Path) -> tuple[ConfigManager, ProfileManager, MCPManager]:
    """Create managers rooted in a temporary directory to avoid touching the real home."""
    base = tmp_path / "home" / ".aidev"

    config_manager = ConfigManager()
    config_manager.aidev_dir = base
    config_manager.config_dir = base / "config"
    config_manager.profiles_dir = config_manager.config_dir / "profiles"
    config_manager.custom_profiles_dir = config_manager.profiles_dir / "custom"
    config_manager.mcp_servers_dir = config_manager.config_dir / "mcp-servers"
    config_manager.custom_mcp_dir = config_manager.mcp_servers_dir / "custom"
    config_manager.memory_banks_dir = base / "memory-banks"
    config_manager.plugins_dir = base / "plugins"
    config_manager.cache_dir = base / "cache"
    config_manager.logs_dir = base / "logs"
    config_manager.env_file = base / ".env"
    config_manager.tools_config = config_manager.config_dir / "tools.json"

    profile_manager = ProfileManager()
    profile_manager.profiles_dir = config_manager.profiles_dir
    profile_manager.custom_profiles_dir = config_manager.custom_profiles_dir

    mcp_manager = MCPManager()
    mcp_manager.mcp_servers_dir = config_manager.mcp_servers_dir
    mcp_manager.custom_mcp_dir = config_manager.custom_mcp_dir
    mcp_manager.cache_dir = config_manager.cache_dir

    return config_manager, profile_manager, mcp_manager


def test_detector_captures_js_signals(tmp_path):
    project_dir = tmp_path / "js-app"
    project_dir.mkdir()
    (project_dir / "package.json").write_text("{}")
    (project_dir / "tsconfig.json").write_text("{}")

    detector = QuickstartDetector(project_dir)
    detections = detector.detect()

    js_detection = next((d for d in detections if d.name == "javascript"), None)
    assert js_detection is not None
    assert js_detection.confidence >= 0.6
    assert any("package.json" in reason for reason in js_detection.reasons)


def test_recommendation_prefers_infra_when_docker_signals(tmp_path):
    config_manager, profile_manager, mcp_manager = _temp_managers(tmp_path)
    config_manager.init_directories()
    profile_manager.init_builtin_profiles()

    runner = QuickstartRunner(config_manager, profile_manager, mcp_manager)
    detections = [
        StackDetection(name="javascript", confidence=0.6, reasons=["Found package.json"]),
        StackDetection(name="docker", confidence=0.8, reasons=["Found docker-compose file"]),
    ]

    recommendation = runner.recommend_profile(detections)
    assert recommendation.tag == "infra"
    assert "docker" in recommendation.rationale
    assert recommendation.profile in profile_manager.list_profiles()


def test_quickstart_creates_project_and_preserves_profile(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "package.json").write_text(json.dumps({"name": "demo"}))

    config_manager, profile_manager, mcp_manager = _temp_managers(tmp_path)
    runner = QuickstartRunner(config_manager, profile_manager, mcp_manager)

    first_run = runner.run(project_dir=project_dir, auto_confirm=True)
    config_path = project_dir / ".aidev"

    assert (config_path / "config.json").exists()
    assert first_run.selected_profile in profile_manager.list_profiles()
    assert (config_path / "profile").read_text().strip() == first_run.selected_profile

    # Change profile manually and rerun to ensure idempotency/preservation
    (config_path / "profile").write_text("custom")
    second_run = runner.run(project_dir=project_dir, auto_confirm=True)
    assert (config_path / "profile").read_text().strip() == "custom"
    assert second_run.selected_profile == "custom"
