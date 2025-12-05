"""
Profile management for aidev
"""
from pathlib import Path
from typing import Optional
from aidev.constants import (
    PROFILES_DIR,
    CUSTOM_PROFILES_DIR,
    BUILTIN_PROFILES,
)
from aidev.models import Profile, MCPServerConfig
from aidev.utils import load_json, save_json, console


class ProfileManager:
    """Manages AI development profiles"""

    def __init__(self) -> None:
        """Initialize profile manager"""
        self.profiles_dir = PROFILES_DIR
        self.custom_profiles_dir = CUSTOM_PROFILES_DIR

    def get_profile_path(self, name: str) -> Optional[Path]:
        """
        Get path to profile file

        Args:
            name: Profile name

        Returns:
            Path to profile file if it exists, None otherwise
        """
        # Check custom profiles first
        custom_path = self.custom_profiles_dir / f"{name}.json"
        if custom_path.exists():
            return custom_path

        # Check built-in profiles
        builtin_path = self.profiles_dir / f"{name}.json"
        if builtin_path.exists():
            return builtin_path

        return None

    def list_profiles(self) -> list[str]:
        """
        List all available profiles

        Returns:
            List of profile names
        """
        profiles = set()

        # Add built-in profiles
        if self.profiles_dir.exists():
            for path in self.profiles_dir.glob("*.json"):
                profiles.add(path.stem)

        # Add custom profiles
        if self.custom_profiles_dir.exists():
            for path in self.custom_profiles_dir.glob("*.json"):
                profiles.add(path.stem)

        return sorted(list(profiles))

    def load_profile(self, name: str) -> Optional[Profile]:
        """
        Load a profile by name

        Args:
            name: Profile name

        Returns:
            Profile object or None if not found
        """
        path = self.get_profile_path(name)
        if not path:
            console.print(f"[red]Profile '{name}' not found[/red]")
            return None

        data = load_json(path)
        if not data:
            return None

        try:
            profile = Profile(**data)

            # If profile extends another, merge them
            if profile.extends:
                base_profile = self.load_profile(profile.extends)
                if base_profile:
                    profile = self._merge_profiles(base_profile, profile)

            return profile
        except Exception as e:
            console.print(f"[red]Error loading profile '{name}': {e}[/red]")
            return None

    def save_profile(self, profile: Profile, custom: bool = True) -> None:
        """
        Save a profile

        Args:
            profile: Profile to save
            custom: Whether to save as custom profile (default: True)
        """
        # Custom profiles go in custom directory
        if custom:
            path = self.custom_profiles_dir / f"{profile.name}.json"
        else:
            path = self.profiles_dir / f"{profile.name}.json"

        save_json(path, profile.model_dump())

    def create_profile(
        self,
        name: str,
        description: str = "",
        extends: Optional[str] = None,
    ) -> Profile:
        """
        Create a new profile

        Args:
            name: Profile name
            description: Profile description
            extends: Base profile to extend from

        Returns:
            Created profile
        """
        profile = Profile(
            name=name,
            description=description,
            extends=extends,
        )

        self.save_profile(profile)
        return profile

    def delete_profile(self, name: str) -> bool:
        """
        Delete a custom profile

        Args:
            name: Profile name

        Returns:
            True if deleted, False otherwise
        """
        if name in BUILTIN_PROFILES:
            console.print(f"[red]Cannot delete built-in profile '{name}'[/red]")
            return False

        path = self.custom_profiles_dir / f"{name}.json"
        if not path.exists():
            console.print(f"[red]Profile '{name}' not found[/red]")
            return False

        path.unlink()
        return True

    def export_profile(self, name: str, output_path: Path) -> bool:
        """
        Export a profile to a file

        Args:
            name: Profile name
            output_path: Output file path

        Returns:
            True if exported, False otherwise
        """
        profile = self.load_profile(name)
        if not profile:
            return False

        save_json(output_path, profile.model_dump())
        return True

    def import_profile(self, input_path: Path) -> Optional[Profile]:
        """
        Import a profile from a file

        Args:
            input_path: Input file path

        Returns:
            Imported profile or None if failed
        """
        data = load_json(input_path)
        if not data:
            return None

        try:
            profile = Profile(**data)
            self.save_profile(profile)
            return profile
        except Exception as e:
            console.print(f"[red]Error importing profile: {e}[/red]")
            return None

    def _merge_profiles(self, base: Profile, override: Profile) -> Profile:
        """
        Merge two profiles (base + overrides)

        Args:
            base: Base profile
            override: Override profile

        Returns:
            Merged profile
        """
        # Start with base profile data
        merged_data = base.model_dump()

        # Override with new profile data (except extends)
        override_data = override.model_dump()
        override_data.pop("extends", None)  # Don't inherit extends

        # Merge MCP servers (by name)
        base_servers = {s.name: s for s in base.mcp_servers}
        override_servers = {s.name: s for s in override.mcp_servers}
        base_servers.update(override_servers)
        merged_data["mcp_servers"] = list(base_servers.values())

        # Merge environment variables
        merged_data["environment"].update(override_data.get("environment", {}))

        # Merge tools
        merged_data["tools"].update(override_data.get("tools", {}))

        # Update other fields
        for key in ["name", "description"]:
            if key in override_data:
                merged_data[key] = override_data[key]

        return Profile(**merged_data)

    def init_builtin_profiles(self) -> None:
        """Initialize built-in profiles if they don't exist"""
        builtin_profiles = self._get_builtin_profiles()

        for profile in builtin_profiles:
            path = self.profiles_dir / f"{profile.name}.json"
            if not path.exists():
                save_json(path, profile.model_dump())

    def _get_builtin_profiles(self) -> list[Profile]:
        """Get built-in profile definitions"""
        return [
            Profile(
                name="default",
                description="General development with essential tools",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="memory-bank", enabled=True),
                ],
            ),
            Profile(
                name="minimal",
                description="Bare minimum configuration",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                ],
            ),
            Profile(
                name="researcher",
                description="Research and investigation workflows",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="duckduckgo", enabled=True),
                    MCPServerConfig(name="memory", enabled=True),
                    MCPServerConfig(name="memory-bank", enabled=True),
                    MCPServerConfig(name="sequential-thinking", enabled=True),
                ],
            ),
            Profile(
                name="fullstack",
                description="Full-stack web development",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="github", enabled=True),
                    MCPServerConfig(name="postgres", enabled=True),
                ],
            ),
            Profile(
                name="devops",
                description="Infrastructure and deployment",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="gitlab", enabled=True),
                    MCPServerConfig(name="k8s", enabled=True),
                    MCPServerConfig(name="atlassian", enabled=True),
                ],
            ),
            Profile(
                name="work",
                description="Work profile with GitLab, Atlassian, and internal MCP tools",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="gitlab", enabled=True),
                    MCPServerConfig(name="cypress", enabled=True),
                    MCPServerConfig(name="atlassian", enabled=True),
                    MCPServerConfig(name="k8s", enabled=True),
                    MCPServerConfig(name="serena", enabled=True),
                    MCPServerConfig(name="heimdall", enabled=True),
                    MCPServerConfig(name="memory-bank", enabled=True),
                    MCPServerConfig(name="duckduckgo", enabled=True),
                    MCPServerConfig(name="sequential-thinking", enabled=True),
                    MCPServerConfig(name="memory", enabled=True),
                    MCPServerConfig(name="compass", enabled=True),
                ],
                environment={
                    "GITLAB_URL": "https://gitlab.checkrhq.net",
                    "GITLAB_API_URL": "https://gitlab.checkrhq.net/api/v4",
                    "MEMORY_BANK_ROOT": "${HOME}/.local/ai-dev/memory-banks",
                },
            ),
            Profile(
                name="data",
                description="Data science and analysis",
                mcp_servers=[
                    MCPServerConfig(name="filesystem", enabled=True),
                    MCPServerConfig(name="git", enabled=True),
                    MCPServerConfig(name="postgres", enabled=True),
                    MCPServerConfig(name="memory-bank", enabled=True),
                ],
            ),
        ]
