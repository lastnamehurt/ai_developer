"""
Constants and default values for aidev
"""
import json
from pathlib import Path
from typing import Final

# Version
VERSION: Final[str] = "0.1.0"

# Directories
HOME_DIR: Final[Path] = Path.home()
AIDEV_DIR: Final[Path] = HOME_DIR / ".aidev"
CONFIG_DIR: Final[Path] = AIDEV_DIR / "config"
PROFILES_DIR: Final[Path] = CONFIG_DIR / "profiles"
CUSTOM_PROFILES_DIR: Final[Path] = PROFILES_DIR / "custom"
MCP_SERVERS_DIR: Final[Path] = CONFIG_DIR / "mcp-servers"
CUSTOM_MCP_DIR: Final[Path] = MCP_SERVERS_DIR / "custom"
MEMORY_BANKS_DIR: Final[Path] = AIDEV_DIR / "memory-banks"
PLUGINS_DIR: Final[Path] = AIDEV_DIR / "plugins"
CACHE_DIR: Final[Path] = AIDEV_DIR / "cache"
LOGS_DIR: Final[Path] = AIDEV_DIR / "logs"

# Bundled data
CONFIGS_DIR: Final[Path] = Path(__file__).parent.parent.parent / "configs"
ENGINEERING_WORKFLOW_TEMPLATE: Final[Path] = CONFIGS_DIR / "engineering-workflow.md"

# Files
ENV_FILE: Final[Path] = AIDEV_DIR / ".env"
TOOLS_CONFIG: Final[Path] = CONFIG_DIR / "tools.json"

# Project-specific
PROJECT_CONFIG_DIR: Final[str] = ".aidev"
PROJECT_CONFIG_FILE: Final[str] = "config.json"
PROJECT_ENV_FILE: Final[str] = ".env"
PROJECT_PROFILE_FILE: Final[str] = "profile"

# Built-in profiles
BUILTIN_PROFILES: Final[list[str]] = [
    "default",
    "minimal",
    "researcher",
    "fullstack",
    "devops",
    "data",
]

def _load_supported_tools() -> dict[str, dict[str, str]]:
    """Load supported tool definitions from bundled JSON."""
    config_file = CONFIGS_DIR / "supported-tools.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Supported tools config missing: {config_file}")
    try:
        return json.loads(config_file.read_text())
    except Exception as exc:
        raise RuntimeError(f"Failed to load supported tools config: {exc}") from exc


SUPPORTED_TOOLS: Final[dict[str, dict[str, str]]] = _load_supported_tools()

# MCP Registry
DEFAULT_MCP_REGISTRY: Final[str] = "https://raw.githubusercontent.com/aidev/mcp-registry/main/registry.json"

# Backup
BACKUP_EXTENSION: Final[str] = ".aidev-backup.tar.gz"
