"""
Configuration management for aidev
"""
import json
import os
from pathlib import Path
from typing import Optional
from aidev.constants import (
    AIDEV_DIR,
    CONFIG_DIR,
    PROFILES_DIR,
    CUSTOM_PROFILES_DIR,
    MCP_SERVERS_DIR,
    CUSTOM_MCP_DIR,
    MEMORY_BANKS_DIR,
    PLUGINS_DIR,
    CACHE_DIR,
    LOGS_DIR,
    ENV_FILE,
    TOOLS_CONFIG,
    SUPPORTED_TOOLS,
    ENGINEERING_WORKFLOW_TEMPLATE,
    PROJECT_CONFIG_DIR,
    PROJECT_ENV_FILE,
    PROJECT_PROFILE_FILE,
)
from aidev.utils import ensure_dir, load_json, save_json, load_env, save_env
from aidev.secrets import decrypt_value, encrypt_value

# Alias used by tests and to allow patching during runtime
GLOBAL_ENV_FILE = ENV_FILE

# Minimal MCP config used when no global config exists
DEFAULT_PROJECT_MCP_CONFIG = {
    "mcpServers": {
        "git": {"command": "git-mcp-server", "args": []},
        "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]},
    }
}


class ConfigManager:
    """Manages aidev configuration and directories

    GitHub Copilot Integration:
    GitHub Copilot is a powerful AI pair programmer that can be leveraged directly within your IDE (like VS Code, JetBrains IDEs, Neovim, and Visual Studio). It offers autocompletion, code suggestions, and even generates entire functions based on your comments and code context.

    Native Integration:
    Copilot integrates natively with GitHub, meaning it understands your repository's context, including issues, pull requests, and codebase. This tight integration allows for more relevant and accurate suggestions.

    Cost:
    GitHub Copilot is a paid subscription service, though it offers a free trial and is free for verified students and maintainers of popular open-source projects. For individual developers, it costs $10/month or $100/year. For businesses, pricing is $19/user/month.
    """

    def __init__(self) -> None:
        """Initialize config manager"""
        self.aidev_dir = AIDEV_DIR
        self.config_dir = CONFIG_DIR
        self.profiles_dir = PROFILES_DIR
        self.custom_profiles_dir = CUSTOM_PROFILES_DIR
        self.mcp_servers_dir = MCP_SERVERS_DIR
        self.custom_mcp_dir = CUSTOM_MCP_DIR
        self.memory_banks_dir = MEMORY_BANKS_DIR
        self.plugins_dir = PLUGINS_DIR
        self.cache_dir = CACHE_DIR
        self.logs_dir = LOGS_DIR
        self.env_file = GLOBAL_ENV_FILE
        self.tools_config = TOOLS_CONFIG
        # Allow tests (and callers) to override the notion of "current directory"
        self._current_dir: Path = Path.cwd()

    def init_directories(self) -> None:
        """Initialize all required directories"""
        directories = [
            self.aidev_dir,
            self.config_dir,
            self.profiles_dir,
            self.custom_profiles_dir,
            self.mcp_servers_dir,
            self.custom_mcp_dir,
            self.memory_banks_dir,
            self.plugins_dir,
            self.cache_dir,
            self.logs_dir,
        ]

        for directory in directories:
            ensure_dir(directory)

        # Seed default env file with a default profile override if missing
        env_vars = load_env(self.env_file)
        if "AIDEV_DEFAULT_PROFILE" not in env_vars:
            env_vars["AIDEV_DEFAULT_PROFILE"] = "default"
            save_env(self.env_file, env_vars)

    def is_initialized(self) -> bool:
        """Check if aidev is initialized"""
        return self.aidev_dir.exists() and self.config_dir.exists()

    def get_env(self, project_dir: Optional[Path] = None) -> dict[str, str]:
        """Get merged environment variables (global, overridden by project), decrypting secrets."""
        global_env = load_env(self.env_file)

        config_path = self.get_project_config_path(project_dir)
        project_env_path = config_path / PROJECT_ENV_FILE if config_path else None
        project_env = load_env(project_env_path) if project_env_path and project_env_path.exists() else {}
        merged = {**global_env, **project_env}

        # Decrypt any encrypted values
        decrypted: dict[str, str] = {}
        for key, value in merged.items():
            _, plaintext = decrypt_value(value)
            decrypted[key] = plaintext
        return decrypted

    def set_env(
        self, key: str, value: str, project: bool = False, project_dir: Optional[Path] = None, encrypt: bool = False
    ) -> None:
        """Set an environment variable (global by default, project if requested)."""
        if project:
            config_path = self.get_project_config_path(project_dir)
            if config_path is None:
                base_dir = project_dir or self._current_dir
                config_path = base_dir / PROJECT_CONFIG_DIR
            env_path = config_path / PROJECT_ENV_FILE
        else:
            env_path = self.env_file
        env_vars = load_env(env_path)
        env_vars[key] = encrypt_value(value) if encrypt else value
        save_env(env_path, env_vars)

    def get_tools_config(self) -> dict:
        """Get tools configuration"""
        return load_json(self.tools_config, default={})

    def save_tools_config(self, config: dict) -> None:
        """Save tools configuration"""
        save_json(self.tools_config, config)

    def get_project_config_path(self, project_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Get project config directory if it exists

        Args:
            project_dir: Project directory (defaults to current directory)

        Returns:
            Path to project config directory or None if not initialized
        """
        base_dir = project_dir or self._current_dir
        config_path = base_dir if base_dir.name == PROJECT_CONFIG_DIR else base_dir / PROJECT_CONFIG_DIR
        return config_path if config_path.exists() else None

    def get_current_profile(self, project_dir: Optional[Path] = None) -> str:
        """Resolve the active profile, preferring project config then env fallback."""
        config_path = self.get_project_config_path(project_dir)
        if config_path:
            profile_file = config_path / PROJECT_PROFILE_FILE
            if profile_file.exists():
                return profile_file.read_text().strip() or "default"
        return os.environ.get("AIDEV_DEFAULT_PROFILE", "default")

    def init_project(
        self, project_dir: Optional[Path] = None, profile: str = "default", profile_name: Optional[str] = None
    ) -> Path:
        """
        Initialize aidev in a project directory

        Args:
            project_dir: Project directory (defaults to current directory)
            profile: Default profile to use
            profile_name: Optional alias for profile (for backward compatibility in tests)

        Returns:
            Path to created config directory
        """
        base_dir = project_dir or self._current_dir or Path.cwd()

        config_path = base_dir / PROJECT_CONFIG_DIR
        ensure_dir(config_path)

        # Create config.json
        config_file = config_path / "config.json"
        if not config_file.exists():
            save_json(config_file, {"profile": profile_name or profile, "environment": {}, "mcp_overrides": {}})

        # Create profile file
        profile_file = config_path / "profile"
        if not profile_file.exists():
            profile_file.write_text(profile_name or profile)

        # Create .env file
        env_file = config_path / ".env"
        if not env_file.exists():
            env_file.touch()

        # Set up project-local tool config folders for legacy compatibility
        self._init_project_tool_configs(base_dir)

        return config_path

    def _init_project_tool_configs(self, project_dir: Path) -> None:
        """Create project-local tool config folders with MCP configs or symlinks back to global configs."""
        tool_dirs = [
            ("claude", "", ""),  # Claude global config lives at ~/.claude.json; no project seed
            ("cursor", ".cursor", "mcp.json"),
        ]

        for tool_id, folder_name, filename in tool_dirs:
            tool_def = SUPPORTED_TOOLS.get(tool_id)
            if not tool_def:
                continue

            global_config_path = Path(os.path.expanduser(tool_def["config_path"]))
            # If no filename, skip creating project-local config (Claude uses global ~/.claude.json)
            if not filename:
                continue

            local_dir = project_dir / folder_name if folder_name else project_dir
            ensure_dir(local_dir)

            local_config_path = local_dir / filename
            if local_config_path.exists():
                # Respect existing files/symlinks
                continue

            if global_config_path.exists():
                try:
                    local_config_path.symlink_to(global_config_path)
                    continue
                except OSError:
                    # Fall back to writing a local file if symlinks are not permitted
                    pass

            # Write a minimal default MCP config if no global file or symlink failed
            save_json(local_config_path, DEFAULT_PROJECT_MCP_CONFIG)

        # Add shared engineering workflow guidance and ensure Cursor summarizes it
        self._ensure_engineering_workflow(project_dir)

    def _ensure_engineering_workflow(self, project_dir: Path) -> None:
        """Place engineering workflow guidance for assistants and add to Cursor rules."""
        claude_dir = project_dir / ".claude"
        ensure_dir(claude_dir)
        workflow_path = claude_dir / "engineering-workflow.md"

        if ENGINEERING_WORKFLOW_TEMPLATE.exists():
            template_content = ENGINEERING_WORKFLOW_TEMPLATE.read_text()
        else:
            template_content = "# Engineering Workflow\n\nDocument your standard engineering workflow here."

        if workflow_path.exists():
            workflow_content = workflow_path.read_text()
        else:
            workflow_content = template_content
            workflow_path.write_text(workflow_content)

        # Copy the workflow to other assistant-specific directories so it is discoverable everywhere
        additional_targets = [
            project_dir / ".aidev" / "engineering-workflow.md",
            project_dir / ".cursor" / "engineering-workflow.md",
            project_dir / ".gemini" / "engineering-workflow.md",
            project_dir / ".codex" / "engineering-workflow.md",
            project_dir / ".zed" / "engineering-workflow.md",
        ]
        for target in additional_targets:
            ensure_dir(target.parent)
            if not target.exists():
                target.write_text(workflow_content)

        # Ensure Cursor summarizes the workflow
        cursor_dir = project_dir / ".cursor"
        ensure_dir(cursor_dir)
        rules_path = cursor_dir / "rules.json"
        default_rules = {
            "include": ["**/*.rb", "**/*.py", "**/*.ts", "**/*.js", "**/*.go", "**/*.md"],
            "exclude": ["node_modules/**", "vendor/**", "log/**", "tmp/**"],
            "summarize": [".claude/engineering-workflow.md"],
            "link": [],
            "rewrite": [],
        }

        rules_data: dict
        if rules_path.exists():
            try:
                rules_data = json.loads(rules_path.read_text())
            except Exception:
                rules_data = default_rules.copy()
        else:
            rules_data = default_rules.copy()

        summarize_list = rules_data.get("summarize", [])
        if ".claude/engineering-workflow.md" not in summarize_list:
            summarize_list.append(".claude/engineering-workflow.md")
        rules_data["summarize"] = summarize_list

        rules_path.write_text(json.dumps(rules_data, indent=2))
