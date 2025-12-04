"""
Backup and restore functionality for aidev
"""
import tarfile
import json
import socket
from pathlib import Path
from datetime import datetime
from typing import Optional
from aidev.constants import (
    AIDEV_DIR,
    PROFILES_DIR,
    CUSTOM_PROFILES_DIR,
    MCP_SERVERS_DIR,
    CUSTOM_MCP_DIR,
    ENV_FILE,
    BACKUP_EXTENSION,
)
from aidev.models import BackupManifest
from aidev.utils import console, confirm


class BackupManager:
    """Manages backup and restore of aidev configuration"""

    def __init__(self) -> None:
        """Initialize backup manager"""
        self.aidev_dir = AIDEV_DIR
        self.backup_extension = BACKUP_EXTENSION

    def create_backup(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Create a backup of aidev configuration

        Args:
            output_path: Optional custom output path

        Returns:
            Path to backup file or None if failed
        """
        if not self.aidev_dir.exists():
            console.print("[red]aidev is not initialized. Nothing to backup.[/red]")
            return None

        # Generate backup filename
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            hostname = socket.gethostname().split(".")[0]
            output_path = Path.cwd() / f"aidev-{hostname}-{timestamp}{self.backup_extension}"

        console.print(f"[cyan]Creating backup: {output_path}[/cyan]")

        # Collect files to backup
        files_to_backup = self._get_backup_files()

        # Create manifest
        manifest = self._create_manifest()

        # Create tar archive
        try:
            with tarfile.open(output_path, "w:gz") as tar:
                # Add manifest
                manifest_json = manifest.model_dump_json(indent=2)
                manifest_bytes = manifest_json.encode("utf-8")

                import io
                manifest_file = io.BytesIO(manifest_bytes)
                info = tarfile.TarInfo(name="manifest.json")
                info.size = len(manifest_bytes)
                tar.addfile(tarinfo=info, fileobj=manifest_file)

                # Add files
                for file_path in files_to_backup:
                    if file_path.exists():
                        arcname = file_path.relative_to(self.aidev_dir)
                        tar.add(file_path, arcname=arcname)

            console.print(f"[green]✓[/green] Backup created: {output_path}")
            console.print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")
            return output_path

        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")
            if output_path.exists():
                output_path.unlink()
            return None

    def restore_backup(self, backup_path: Path, force: bool = False) -> bool:
        """
        Restore aidev configuration from backup

        Args:
            backup_path: Path to backup file
            force: Force restore without confirmation

        Returns:
            True if restored successfully, False otherwise
        """
        if not backup_path.exists():
            console.print(f"[red]Backup file not found: {backup_path}[/red]")
            return False

        # Read manifest
        manifest = self._read_manifest(backup_path)
        if not manifest:
            console.print("[red]Invalid backup file (no manifest)[/red]")
            return False

        # Display backup info
        console.print("\n[bold]Backup Information:[/bold]")
        console.print(f"  Version: {manifest.version}")
        console.print(f"  Created: {manifest.created_at}")
        console.print(f"  Hostname: {manifest.hostname}")
        console.print(f"  Profiles: {len(manifest.profiles)}")
        console.print(f"  MCP Servers: {len(manifest.mcp_servers)}")
        console.print(f"  Environment: {'Yes' if manifest.has_env else 'No'}\n")

        # Confirm restore
        if not force:
            if self.aidev_dir.exists():
                console.print("[yellow]Warning: This will overwrite your current configuration![/yellow]")
                if not confirm("Continue with restore?", default=False):
                    console.print("Restore cancelled")
                    return False

        # Extract backup
        try:
            console.print("[cyan]Restoring configuration...[/cyan]")

            with tarfile.open(backup_path, "r:gz") as tar:
                # Extract all files except manifest
                members = [m for m in tar.getmembers() if m.name != "manifest.json"]
                tar.extractall(path=self.aidev_dir, members=members)

            console.print("[green]✓[/green] Configuration restored successfully")
            console.print("\nRestored:")
            for profile in manifest.profiles:
                console.print(f"  • Profile: {profile}")
            for server in manifest.mcp_servers:
                console.print(f"  • MCP Server: {server}")

            return True

        except Exception as e:
            console.print(f"[red]Error restoring backup: {e}[/red]")
            return False

    def export_config(self, output_path: Path) -> bool:
        """
        Export configuration for sharing (without sensitive data)

        Args:
            output_path: Output file path

        Returns:
            True if exported successfully, False otherwise
        """
        export_data = {
            "profiles": {},
            "mcp_servers": {},
        }

        # Export custom profiles
        if CUSTOM_PROFILES_DIR.exists():
            for profile_file in CUSTOM_PROFILES_DIR.glob("*.json"):
                with open(profile_file) as f:
                    export_data["profiles"][profile_file.stem] = json.load(f)

        # Export custom MCP servers
        if CUSTOM_MCP_DIR.exists():
            for server_file in CUSTOM_MCP_DIR.glob("*.json"):
                with open(server_file) as f:
                    export_data["mcp_servers"][server_file.stem] = json.load(f)

        try:
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

            console.print(f"[green]✓[/green] Configuration exported: {output_path}")
            return True

        except Exception as e:
            console.print(f"[red]Error exporting configuration: {e}[/red]")
            return False

    def import_config(self, input_path: Path) -> bool:
        """
        Import shared configuration

        Args:
            input_path: Input file path

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(input_path) as f:
                import_data = json.load(f)

            imported_count = 0

            # Import profiles
            for name, profile_data in import_data.get("profiles", {}).items():
                profile_file = CUSTOM_PROFILES_DIR / f"{name}.json"
                with open(profile_file, "w") as f:
                    json.dump(profile_data, f, indent=2)
                console.print(f"[green]✓[/green] Imported profile: {name}")
                imported_count += 1

            # Import MCP servers
            for name, server_data in import_data.get("mcp_servers", {}).items():
                server_file = CUSTOM_MCP_DIR / f"{name}.json"
                with open(server_file, "w") as f:
                    json.dump(server_data, f, indent=2)
                console.print(f"[green]✓[/green] Imported MCP server: {name}")
                imported_count += 1

            console.print(f"\n[bold green]Imported {imported_count} items[/bold green]")
            return True

        except Exception as e:
            console.print(f"[red]Error importing configuration: {e}[/red]")
            return False

    def _get_backup_files(self) -> list[Path]:
        """Get list of files to include in backup"""
        files = []

        # Profiles
        if PROFILES_DIR.exists():
            files.extend(PROFILES_DIR.glob("*.json"))
        if CUSTOM_PROFILES_DIR.exists():
            files.extend(CUSTOM_PROFILES_DIR.glob("*.json"))

        # MCP servers
        if MCP_SERVERS_DIR.exists():
            files.extend(MCP_SERVERS_DIR.glob("*.json"))
        if CUSTOM_MCP_DIR.exists():
            files.extend(CUSTOM_MCP_DIR.glob("*.json"))

        # Environment file (if exists)
        if ENV_FILE.exists():
            files.append(ENV_FILE)

        return files

    def _create_manifest(self) -> BackupManifest:
        """Create backup manifest"""
        profiles = []
        if CUSTOM_PROFILES_DIR.exists():
            profiles = [p.stem for p in CUSTOM_PROFILES_DIR.glob("*.json")]

        mcp_servers = []
        if CUSTOM_MCP_DIR.exists():
            mcp_servers = [s.stem for s in CUSTOM_MCP_DIR.glob("*.json")]

        return BackupManifest(
            version=self._get_version(),
            created_at=datetime.now().isoformat(),
            hostname=socket.gethostname(),
            profiles=profiles,
            mcp_servers=mcp_servers,
            has_env=ENV_FILE.exists(),
        )

    def _read_manifest(self, backup_path: Path) -> Optional[BackupManifest]:
        """Read manifest from backup file"""
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                manifest_file = tar.extractfile("manifest.json")
                if manifest_file:
                    manifest_data = json.load(manifest_file)
                    return BackupManifest(**manifest_data)
        except Exception:
            pass

        return None

    def _get_version(self) -> str:
        """Get aidev version"""
        from aidev import __version__
        return __version__
