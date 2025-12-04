"""
Unit tests for profile management
"""
import pytest
from pathlib import Path
from aidev.profiles import ProfileManager
from aidev.models import Profile, MCPServerConfig
from aidev.constants import SUPPORTED_TOOLS


class TestProfileManager:
    """Test ProfileManager class"""

    def test_create_profile(self, tmp_path):
        """Test creating a new profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path

        profile = manager.create_profile(
            name="test-profile",
            description="Test profile",
        )

        assert profile.name == "test-profile"
        assert profile.description == "Test profile"
        assert (tmp_path / "test-profile.json").exists()

    def test_load_profile(self, tmp_path):
        """Test loading a profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path

        # Create profile
        profile = Profile(
            name="test",
            description="Test",
            mcp_servers=[
                MCPServerConfig(name="filesystem", enabled=True)
            ],
        )
        manager.save_profile(profile)

        # Load profile
        loaded = manager.load_profile("test")
        assert loaded is not None
        assert loaded.name == "test"
        assert len(loaded.mcp_servers) == 1

    def test_list_profiles(self, tmp_path):
        """Test listing profiles"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path
        manager.custom_profiles_dir = tmp_path / "custom"
        manager.custom_profiles_dir.mkdir()

        # Create some profiles
        for name in ["profile1", "profile2", "profile3"]:
            profile = Profile(name=name, description="Test")
            manager.save_profile(profile)

        profiles = manager.list_profiles()
        assert len(profiles) == 3
        assert "profile1" in profiles
        assert "profile2" in profiles
        assert "profile3" in profiles

    def test_merge_profiles(self, tmp_path):
        """Test profile inheritance"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path

        # Create base profile
        base = Profile(
            name="base",
            description="Base profile",
            mcp_servers=[
                MCPServerConfig(name="filesystem", enabled=True)
            ],
            environment={"KEY1": "value1"},
        )

        # Create extending profile
        extended = Profile(
            name="extended",
            description="Extended profile",
            extends="base",
            mcp_servers=[
                MCPServerConfig(name="git", enabled=True)
            ],
            environment={"KEY2": "value2"},
        )

        # Merge
        merged = manager._merge_profiles(base, extended)

        assert merged.name == "extended"
        assert len(merged.mcp_servers) == 2
        assert "KEY1" in merged.environment
        assert "KEY2" in merged.environment

    def test_builtin_profiles(self):
        """Test built-in profile definitions"""
        manager = ProfileManager()
        builtin = manager._get_builtin_profiles()

        assert len(builtin) > 0

        # Check that default profile exists
        default = next((p for p in builtin if p.name == "default"), None)
        assert default is not None
        assert default.description
        assert len(default.mcp_servers) > 0

    def test_supported_tools_loaded(self):
        """Ensure supported tools are loaded from JSON or fallback."""
        assert "cursor" in SUPPORTED_TOOLS
        assert "gemini" in SUPPORTED_TOOLS
