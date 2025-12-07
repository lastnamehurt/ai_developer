"""
Unit tests for profile management
"""
import pytest
from pathlib import Path
from unittest.mock import patch
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

        # Check expected modern profiles
        names = {p.name for p in builtin}
        assert {"default", "web", "qa", "infra"} <= names

        default = next((p for p in builtin if p.name == "default"), None)
        assert default is not None
        assert default.extends == "web"

    def test_supported_tools_loaded(self):
        """Ensure supported tools are loaded from JSON or fallback."""
        assert "cursor" in SUPPORTED_TOOLS
        assert "gemini" in SUPPORTED_TOOLS

    def test_load_profile_not_found(self, tmp_path):
        """Test loading a non-existent profile"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path
        manager.custom_profiles_dir = tmp_path / "custom"

        profile = manager.load_profile("nonexistent")
        assert profile is None

    def test_load_profile_with_inheritance(self, tmp_path):
        """Test loading profile with extends"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path
        manager.custom_profiles_dir = tmp_path / "custom"
        manager.custom_profiles_dir.mkdir()

        # Create base profile
        base = Profile(
            name="base",
            description="Base",
            mcp_servers=[MCPServerConfig(name="git", enabled=True)],
            environment={"BASE_VAR": "base"},
        )
        manager.save_profile(base)

        # Create child profile
        child = Profile(
            name="child",
            description="Child",
            extends="base",
            mcp_servers=[MCPServerConfig(name="github", enabled=True)],
            environment={"CHILD_VAR": "child"},
        )
        manager.save_profile(child)

        # Load child - should include base servers and env
        loaded = manager.load_profile("child")
        assert loaded is not None
        assert len(loaded.mcp_servers) == 2
        assert "BASE_VAR" in loaded.environment
        assert "CHILD_VAR" in loaded.environment

    def test_get_profile_path_custom_first(self, tmp_path):
        """Test that custom profiles take precedence"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path / "builtin"
        manager.custom_profiles_dir = tmp_path / "custom"
        manager.profiles_dir.mkdir()
        manager.custom_profiles_dir.mkdir()

        # Create same-named profile in both locations
        (manager.profiles_dir / "test.json").write_text('{"name":"test"}')
        (manager.custom_profiles_dir / "test.json").write_text('{"name":"custom"}')

        path = manager.get_profile_path("test")
        assert path == manager.custom_profiles_dir / "test.json"

    def test_get_profile_path_none(self, tmp_path):
        """Test getting path for non-existent profile"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path
        manager.custom_profiles_dir = tmp_path / "custom"

        path = manager.get_profile_path("nonexistent")
        assert path is None

    def test_save_profile_custom(self, tmp_path):
        """Test saving as custom profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(parents=True, exist_ok=True)

        profile = Profile(name="test", description="Test")
        manager.save_profile(profile, custom=True)

        assert (tmp_path / "test.json").exists()

    def test_save_profile_builtin(self, tmp_path):
        """Test saving as builtin profile"""
        manager = ProfileManager()
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(parents=True, exist_ok=True)

        profile = Profile(name="test", description="Test")
        manager.save_profile(profile, custom=False)

        assert (tmp_path / "test.json").exists()

    def test_clone_profile_success(self, tmp_path):
        """Test cloning a profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path / "builtin"
        manager.custom_profiles_dir.mkdir(exist_ok=True)
        manager.profiles_dir.mkdir(exist_ok=True)

        # Create source profile
        source = Profile(
            name="source",
            description="Source profile",
            mcp_servers=[MCPServerConfig(name="git", enabled=True)],
        )
        manager.save_profile(source)

        # Clone it
        with patch("aidev.profiles.console"):
            cloned = manager.clone_profile("source", "cloned")

        assert cloned is not None
        assert cloned.name == "cloned"
        assert cloned.description == "Cloned from source"
        assert len(cloned.mcp_servers) == 1
        assert (tmp_path / "cloned.json").exists()

    def test_clone_profile_with_description(self, tmp_path):
        """Test cloning with custom description"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        source = Profile(name="source", description="Original")
        manager.save_profile(source)

        with patch("aidev.profiles.console"):
            cloned = manager.clone_profile("source", "cloned", description="Custom description")

        assert cloned is not None
        assert cloned.description == "Custom description"

    def test_clone_profile_target_exists(self, tmp_path):
        """Test cloning when target already exists"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create both profiles
        source = Profile(name="source", description="Source")
        target = Profile(name="target", description="Target")
        manager.save_profile(source)
        manager.save_profile(target)

        with patch("aidev.profiles.console") as mock_console:
            cloned = manager.clone_profile("source", "target")

        assert cloned is None
        mock_console.print.assert_called_once()

    def test_clone_profile_source_not_found(self, tmp_path):
        """Test cloning non-existent profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        with patch("aidev.profiles.console"):
            cloned = manager.clone_profile("nonexistent", "new")

        assert cloned is None

    def test_delete_profile_success(self, tmp_path):
        """Test deleting a custom profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create profile
        profile = Profile(name="test", description="Test")
        manager.save_profile(profile)
        assert (tmp_path / "test.json").exists()

        # Delete it
        with patch("aidev.profiles.console"):
            result = manager.delete_profile("test")

        assert result is True
        assert not (tmp_path / "test.json").exists()

    def test_delete_profile_builtin(self, tmp_path):
        """Test deleting builtin profile fails"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path

        with patch("aidev.profiles.console") as mock_console:
            result = manager.delete_profile("default")

        assert result is False
        mock_console.print.assert_called_once()

    def test_delete_profile_not_found(self, tmp_path):
        """Test deleting non-existent profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        with patch("aidev.profiles.console") as mock_console:
            result = manager.delete_profile("nonexistent")

        assert result is False
        mock_console.print.assert_called_once()

    # TODO: Fix these tests - they need proper mocking
    # def test_delete_profile(self, tmp_path):
    #     """Test deleting a profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #     tmp_path.mkdir(exist_ok=True)
    #
    #     # Create and save profile
    #     profile = Profile(name="test", description="Test")
    #     manager.save_profile(profile)
    #     assert (tmp_path / "test.json").exists()
    #
    #     # Delete it
    #     result = manager.delete_profile("test")
    #     assert result is True
    #     assert not (tmp_path / "test.json").exists()

    # def test_delete_profile_not_found(self, tmp_path):
    #     """Test deleting non-existent profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #
    #     result = manager.delete_profile("nonexistent")
    #     assert result is False

    # def test_clone_profile(self, tmp_path):
    #     """Test cloning a profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #     manager.profiles_dir = tmp_path / "builtin"
    #     manager.custom_profiles_dir.mkdir()
    #     manager.profiles_dir.mkdir()
    #
    #     # Create source profile
    #     source = Profile(
    #         name="source",
    #         description="Source profile",
    #         mcp_servers=[MCPServerConfig(name="git", enabled=True)],
    #     )
    #     manager.save_profile(source)
    #
    #     # Clone it
    #     cloned = manager.clone_profile("source", "cloned")
    #     assert cloned is not None
    #     assert cloned.name == "cloned"
    #     assert len(cloned.mcp_servers) == 1
    #     assert (tmp_path / "cloned.json").exists()

    # def test_clone_profile_not_found(self, tmp_path):
    #     """Test cloning non-existent profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #     manager.profiles_dir = tmp_path
    #
    #     cloned = manager.clone_profile("nonexistent", "new")
    #     assert cloned is None

    def test_merge_profiles_mcp_override(self):
        """Test MCP server override in merge"""
        manager = ProfileManager()

        base = Profile(
            name="base",
            description="Base",
            mcp_servers=[
                MCPServerConfig(name="git", enabled=True),
                MCPServerConfig(name="github", enabled=True),
            ],
        )

        child = Profile(
            name="child",
            description="Child",
            mcp_servers=[
                MCPServerConfig(name="github", enabled=False),  # Override
                MCPServerConfig(name="gitlab", enabled=True),  # New
            ],
        )

        merged = manager._merge_profiles(base, child)

        # Should have git (from base), github (overridden), gitlab (new)
        assert len(merged.mcp_servers) == 3
        server_names = {s.name for s in merged.mcp_servers}
        assert server_names == {"git", "github", "gitlab"}

        # Check github is disabled (child override)
        github = next(s for s in merged.mcp_servers if s.name == "github")
        assert github.enabled is False

    def test_merge_profiles_tags(self):
        """Test tag merging"""
        manager = ProfileManager()

        base = Profile(
            name="base",
            description="Base",
            tags=["tag1", "tag2"],
        )

        child = Profile(
            name="child",
            description="Child",
            tags=["tag2", "tag3"],
        )

        merged = manager._merge_profiles(base, child)

        # Tags should be unioned
        assert set(merged.tags) == {"tag1", "tag2", "tag3"}

    # TODO: Fix these tests - they need proper mocking
    # def test_init_builtin_profiles(self, tmp_path):
    #     """Test initializing builtin profiles"""
    #     manager = ProfileManager()
    #     manager.profiles_dir = tmp_path
    #     tmp_path.mkdir(exist_ok=True)
    #
    #     manager.init_builtin_profiles()
    #
    #     # Check that builtin profiles were created
    #     profiles = list(tmp_path.glob("*.json"))
    #     assert len(profiles) > 0

    # def test_export_profile(self, tmp_path):
    #     """Test exporting a profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path / "custom"
    #     manager.custom_profiles_dir.mkdir(parents=True)
    #
    #     # Create profile
    #     profile = Profile(
    #         name="test",
    #         description="Test",
    #         mcp_servers=[MCPServerConfig(name="git", enabled=True)],
    #     )
    #     manager.save_profile(profile)
    #
    #     # Export
    #     output = tmp_path / "exported.json"
    #     result = manager.export_profile("test", output)
    #
    #     assert result is True
    #     assert output.exists()

    # def test_export_profile_not_found(self, tmp_path):
    #     """Test exporting non-existent profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #
    #     output = tmp_path / "exported.json"
    #     result = manager.export_profile("nonexistent", output)
    #
    #     assert result is False

    # def test_import_profile(self, tmp_path):
    #     """Test importing a profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #     tmp_path.mkdir(exist_ok=True)
    #
    #     # Create export file
    #     import json
    #     export_data = {
    #         "name": "imported",
    #         "description": "Imported",
    #         "mcp_servers": []
    #     }
    #     export_file = tmp_path / "import.json"
    #     export_file.write_text(json.dumps(export_data))
    #
    #     # Import
    #     result = manager.import_profile(export_file)
    #
    #     assert result is True
    #     assert (tmp_path / "imported.json").exists()

    # def test_import_profile_invalid(self, tmp_path):
    #     """Test importing invalid profile"""
    #     manager = ProfileManager()
    #     manager.custom_profiles_dir = tmp_path
    #
    #     # Create invalid export file
    #     export_file = tmp_path / "invalid.json"
    #     export_file.write_text("not json")
    #
    #     result = manager.import_profile(export_file)
    #
    #     assert result is False

    def test_export_profile_success(self, tmp_path):
        """Test exporting a profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create profile
        profile = Profile(
            name="test",
            description="Test",
            mcp_servers=[MCPServerConfig(name="git", enabled=True)],
        )
        manager.save_profile(profile)

        # Export
        output = tmp_path / "exported.json"
        result = manager.export_profile("test", output)

        assert result is True
        assert output.exists()

    def test_export_profile_not_found(self, tmp_path):
        """Test exporting non-existent profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        output = tmp_path / "exported.json"
        result = manager.export_profile("nonexistent", output)

        assert result is False

    def test_import_profile_success(self, tmp_path):
        """Test importing a profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create export file
        import json
        export_data = {
            "name": "imported",
            "description": "Imported",
            "mcp_servers": [],
            "environment": {},
            "tags": [],
        }
        export_file = tmp_path / "import.json"
        export_file.write_text(json.dumps(export_data))

        # Import
        result = manager.import_profile(export_file)

        assert result is not None
        assert result.name == "imported"
        assert (tmp_path / "imported.json").exists()

    def test_import_profile_invalid(self, tmp_path):
        """Test importing invalid profile"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create invalid export file
        export_file = tmp_path / "invalid.json"
        export_file.write_text("not json")

        from unittest.mock import patch
        with patch("aidev.profiles.console"):
            result = manager.import_profile(export_file)

        assert result is None

    def test_diff_profiles(self, tmp_path):
        """Test comparing two profiles"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        # Create two profiles
        profile1 = Profile(
            name="profile1",
            description="Profile 1",
            mcp_servers=[
                MCPServerConfig(name="git", enabled=True),
                MCPServerConfig(name="github", enabled=True),
            ],
            environment={"VAR1": "value1"},
        )
        profile2 = Profile(
            name="profile2",
            description="Profile 2",
            mcp_servers=[
                MCPServerConfig(name="git", enabled=True),
                MCPServerConfig(name="gitlab", enabled=True),
            ],
            environment={"VAR2": "value2"},
        )
        manager.save_profile(profile1)
        manager.save_profile(profile2)

        # Diff them
        diff = manager.diff_profiles("profile1", "profile2")

        assert diff is not None
        assert "mcp_servers" in diff
        assert "environment" in diff
        assert "tags" in diff
        assert diff["profile1"] == "profile1"
        assert diff["profile2"] == "profile2"

    def test_diff_profiles_not_found(self, tmp_path):
        """Test diffing when profile not found"""
        manager = ProfileManager()
        manager.custom_profiles_dir = tmp_path
        manager.profiles_dir = tmp_path
        tmp_path.mkdir(exist_ok=True)

        diff = manager.diff_profiles("nonexistent1", "nonexistent2")

        assert diff is None
