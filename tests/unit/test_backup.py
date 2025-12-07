"""
Tests for backup.py
"""
import json
import tarfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from aidev.backup import BackupManager
from aidev.constants import (
    CUSTOM_PROFILES_DIR,
    CUSTOM_MCP_DIR,
    ENV_FILE,
)


@pytest.fixture
def backup_manager(tmp_path, monkeypatch):
    """Create BackupManager with temporary directories"""
    aidev_dir = tmp_path / ".aidev"
    aidev_dir.mkdir()

    # Mock constants to use tmp_path
    monkeypatch.setattr("aidev.backup.AIDEV_DIR", aidev_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", aidev_dir / "config" / "profiles" / "custom")
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", aidev_dir / "config" / "mcp-servers" / "custom")
    monkeypatch.setattr("aidev.backup.ENV_FILE", aidev_dir / ".env")
    monkeypatch.setattr("aidev.backup.PROFILES_DIR", aidev_dir / "config" / "profiles")
    monkeypatch.setattr("aidev.backup.MCP_SERVERS_DIR", aidev_dir / "config" / "mcp-servers")

    manager = BackupManager()
    manager.aidev_dir = aidev_dir
    return manager


def test_create_backup_not_initialized(tmp_path, monkeypatch):
    """Test backup creation when aidev not initialized"""
    aidev_dir = tmp_path / ".aidev_nonexistent"
    monkeypatch.setattr("aidev.backup.AIDEV_DIR", aidev_dir)

    manager = BackupManager()
    manager.aidev_dir = aidev_dir

    result = manager.create_backup()
    assert result is None


def test_create_backup_success(backup_manager, tmp_path, monkeypatch):
    """Test successful backup creation"""
    # Create some test files
    profiles_dir = backup_manager.aidev_dir / "config" / "profiles" / "custom"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "test.json").write_text('{"name": "test"}')

    mcp_dir = backup_manager.aidev_dir / "config" / "mcp-servers" / "custom"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "server.json").write_text('{"command": "test"}')

    env_file = backup_manager.aidev_dir / ".env"
    env_file.write_text("KEY=value")

    # Mock to use tmp_path references
    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", profiles_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", mcp_dir)
    monkeypatch.setattr("aidev.backup.ENV_FILE", env_file)
    monkeypatch.setattr("aidev.backup.PROFILES_DIR", backup_manager.aidev_dir / "config" / "profiles")
    monkeypatch.setattr("aidev.backup.MCP_SERVERS_DIR", backup_manager.aidev_dir / "config" / "mcp-servers")

    output_path = tmp_path / "backup.tar.gz"

    with patch("aidev.backup.console"):
        result = backup_manager.create_backup(output_path)

    assert result == output_path
    assert output_path.exists()

    # Verify backup contains expected files
    with tarfile.open(output_path, "r:gz") as tar:
        names = tar.getnames()
        assert "manifest.json" in names
        assert any("test.json" in name for name in names)


def test_create_backup_with_exception(backup_manager, tmp_path, monkeypatch):
    """Test backup creation handles exceptions"""
    output_path = tmp_path / "backup.tar.gz"

    with patch("tarfile.open", side_effect=Exception("Test error")):
        with patch("aidev.backup.console"):
            result = backup_manager.create_backup(output_path)

    assert result is None
    assert not output_path.exists()


def test_restore_backup_file_not_found(backup_manager, tmp_path):
    """Test restore with non-existent backup file"""
    backup_path = tmp_path / "nonexistent.tar.gz"

    with patch("aidev.backup.console"):
        result = backup_manager.restore_backup(backup_path)

    assert result is False


def test_restore_backup_invalid_manifest(backup_manager, tmp_path):
    """Test restore with invalid backup (no manifest)"""
    backup_path = tmp_path / "invalid.tar.gz"

    # Create a tar file without manifest
    with tarfile.open(backup_path, "w:gz") as tar:
        pass

    with patch("aidev.backup.console"):
        result = backup_manager.restore_backup(backup_path)

    assert result is False


def test_restore_backup_success_with_force(backup_manager, tmp_path, monkeypatch):
    """Test successful backup restore with force flag"""
    # Create a valid backup
    backup_path = tmp_path / "backup.tar.gz"

    manifest = {
        "version": "0.1.0",
        "created_at": "2024-01-01T00:00:00",
        "hostname": "test",
        "profiles": ["test"],
        "mcp_servers": ["server"],
        "has_env": True
    }

    with tarfile.open(backup_path, "w:gz") as tar:
        # Add manifest
        import io
        manifest_json = json.dumps(manifest, indent=2)
        manifest_bytes = manifest_json.encode("utf-8")
        manifest_file = io.BytesIO(manifest_bytes)
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(tarinfo=info, fileobj=manifest_file)

        # Add a test file
        test_content = b'{"name": "test"}'
        test_file = io.BytesIO(test_content)
        info = tarfile.TarInfo(name="config/profiles/custom/test.json")
        info.size = len(test_content)
        tar.addfile(tarinfo=info, fileobj=test_file)

    with patch("aidev.backup.console"):
        result = backup_manager.restore_backup(backup_path, force=True)

    assert result is True


def test_restore_backup_cancelled_by_user(backup_manager, tmp_path):
    """Test restore cancelled by user confirmation"""
    backup_path = tmp_path / "backup.tar.gz"

    manifest = {
        "version": "0.1.0",
        "created_at": "2024-01-01T00:00:00",
        "hostname": "test",
        "profiles": [],
        "mcp_servers": [],
        "has_env": False
    }

    with tarfile.open(backup_path, "w:gz") as tar:
        import io
        manifest_json = json.dumps(manifest, indent=2)
        manifest_bytes = manifest_json.encode("utf-8")
        manifest_file = io.BytesIO(manifest_bytes)
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(tarinfo=info, fileobj=manifest_file)

    with patch("aidev.backup.console"):
        with patch("aidev.backup.confirm", return_value=False):
            result = backup_manager.restore_backup(backup_path, force=False)

    assert result is False


def test_restore_backup_with_exception(backup_manager, tmp_path):
    """Test restore handles extraction exceptions"""
    backup_path = tmp_path / "backup.tar.gz"

    manifest = {
        "version": "0.1.0",
        "created_at": "2024-01-01T00:00:00",
        "hostname": "test",
        "profiles": [],
        "mcp_servers": [],
        "has_env": False
    }

    with tarfile.open(backup_path, "w:gz") as tar:
        import io
        manifest_json = json.dumps(manifest, indent=2)
        manifest_bytes = manifest_json.encode("utf-8")
        manifest_file = io.BytesIO(manifest_bytes)
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(tarinfo=info, fileobj=manifest_file)

    with patch("aidev.backup.console"):
        with patch("tarfile.open") as mock_open:
            # Make it succeed for _read_manifest but fail for extraction
            mock_open.side_effect = [
                tarfile.open(backup_path, "r:gz"),  # First call for manifest
                Exception("Extraction failed")  # Second call for restore
            ]
            result = backup_manager.restore_backup(backup_path, force=True)

    assert result is False


def test_export_config_success(backup_manager, tmp_path, monkeypatch):
    """Test successful config export"""
    # Create test files
    profiles_dir = backup_manager.aidev_dir / "config" / "profiles" / "custom"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "myprofile.json").write_text('{"name": "myprofile"}')

    mcp_dir = backup_manager.aidev_dir / "config" / "mcp-servers" / "custom"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "myserver.json").write_text('{"command": "test"}')

    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", profiles_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", mcp_dir)

    output_path = tmp_path / "export.json"

    with patch("aidev.backup.console"):
        result = backup_manager.export_config(output_path)

    assert result is True
    assert output_path.exists()

    # Verify content
    with open(output_path) as f:
        data = json.load(f)

    assert "profiles" in data
    assert "mcp_servers" in data
    assert "myprofile" in data["profiles"]
    assert "myserver" in data["mcp_servers"]


def test_export_config_with_exception(backup_manager, tmp_path, monkeypatch):
    """Test export handles exceptions"""
    output_path = tmp_path / "readonly" / "export.json"

    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", tmp_path / "nonexistent")
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", tmp_path / "nonexistent")

    with patch("aidev.backup.console"):
        result = backup_manager.export_config(output_path)

    assert result is False


def test_import_config_success(backup_manager, tmp_path, monkeypatch):
    """Test successful config import"""
    # Create import file
    import_data = {
        "profiles": {
            "imported": {"name": "imported", "description": "Test"}
        },
        "mcp_servers": {
            "imported_server": {"command": "test"}
        }
    }

    input_path = tmp_path / "import.json"
    with open(input_path, "w") as f:
        json.dump(import_data, f)

    # Setup directories
    profiles_dir = backup_manager.aidev_dir / "config" / "profiles" / "custom"
    profiles_dir.mkdir(parents=True)
    mcp_dir = backup_manager.aidev_dir / "config" / "mcp-servers" / "custom"
    mcp_dir.mkdir(parents=True)

    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", profiles_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", mcp_dir)

    with patch("aidev.backup.console"):
        result = backup_manager.import_config(input_path)

    assert result is True
    assert (profiles_dir / "imported.json").exists()
    assert (mcp_dir / "imported_server.json").exists()


def test_import_config_with_exception(backup_manager, tmp_path):
    """Test import handles exceptions"""
    input_path = tmp_path / "nonexistent.json"

    with patch("aidev.backup.console"):
        result = backup_manager.import_config(input_path)

    assert result is False


def test_get_backup_files(backup_manager, tmp_path, monkeypatch):
    """Test getting list of backup files"""
    # Create test files
    profiles_dir = backup_manager.aidev_dir / "config" / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "builtin.json").write_text("{}")

    custom_profiles = backup_manager.aidev_dir / "config" / "profiles" / "custom"
    custom_profiles.mkdir(parents=True)
    (custom_profiles / "custom.json").write_text("{}")

    mcp_dir = backup_manager.aidev_dir / "config" / "mcp-servers"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "server.json").write_text("{}")

    env_file = backup_manager.aidev_dir / ".env"
    env_file.write_text("KEY=value")

    monkeypatch.setattr("aidev.backup.PROFILES_DIR", profiles_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", custom_profiles)
    monkeypatch.setattr("aidev.backup.MCP_SERVERS_DIR", mcp_dir)
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", backup_manager.aidev_dir / "config" / "mcp-servers" / "custom")
    monkeypatch.setattr("aidev.backup.ENV_FILE", env_file)

    files = backup_manager._get_backup_files()

    assert len(files) >= 3
    assert env_file in files


def test_create_manifest(backup_manager, tmp_path, monkeypatch):
    """Test manifest creation"""
    custom_profiles = backup_manager.aidev_dir / "config" / "profiles" / "custom"
    custom_profiles.mkdir(parents=True)
    (custom_profiles / "test.json").write_text("{}")

    custom_mcp = backup_manager.aidev_dir / "config" / "mcp-servers" / "custom"
    custom_mcp.mkdir(parents=True)
    (custom_mcp / "server.json").write_text("{}")

    env_file = backup_manager.aidev_dir / ".env"
    env_file.write_text("KEY=value")

    monkeypatch.setattr("aidev.backup.CUSTOM_PROFILES_DIR", custom_profiles)
    monkeypatch.setattr("aidev.backup.CUSTOM_MCP_DIR", custom_mcp)
    monkeypatch.setattr("aidev.backup.ENV_FILE", env_file)

    manifest = backup_manager._create_manifest()

    assert manifest.version == "0.1.0"
    assert "test" in manifest.profiles
    assert "server" in manifest.mcp_servers
    assert manifest.has_env is True


def test_read_manifest(backup_manager, tmp_path):
    """Test reading manifest from backup"""
    backup_path = tmp_path / "backup.tar.gz"

    manifest_data = {
        "version": "0.1.0",
        "created_at": "2024-01-01T00:00:00",
        "hostname": "test",
        "profiles": ["test"],
        "mcp_servers": [],
        "has_env": True
    }

    with tarfile.open(backup_path, "w:gz") as tar:
        import io
        manifest_json = json.dumps(manifest_data)
        manifest_bytes = manifest_json.encode("utf-8")
        manifest_file = io.BytesIO(manifest_bytes)
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(tarinfo=info, fileobj=manifest_file)

    manifest = backup_manager._read_manifest(backup_path)

    assert manifest is not None
    assert manifest.version == "0.1.0"
    assert manifest.hostname == "test"
    assert manifest.has_env is True


def test_read_manifest_invalid(backup_manager, tmp_path):
    """Test reading manifest from invalid backup"""
    backup_path = tmp_path / "invalid.tar.gz"

    # Create empty tar
    with tarfile.open(backup_path, "w:gz") as tar:
        pass

    manifest = backup_manager._read_manifest(backup_path)
    assert manifest is None
