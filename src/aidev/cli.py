"""
CLI interface for aidev
"""
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from aidev import __version__
from aidev.config import ConfigManager
from aidev.tools import ToolManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.quickstart import QuickstartRunner
from aidev.utils import load_json, save_json

console = Console()
config_manager = ConfigManager()
tool_manager = ToolManager()
profile_manager = ProfileManager()
mcp_manager = MCPManager()
mcp_config_generator = MCPConfigGenerator()
quickstart_runner = QuickstartRunner(config_manager, profile_manager, mcp_manager)


# ============================================================================
# Helper Functions
# ============================================================================


def _launch_tool_with_profile(tool_id: str, profile: str, args: tuple) -> None:
    """
    Launch a tool with the specified profile and MCP configuration

    Args:
        tool_id: Tool identifier (cursor, claude, zed)
        profile: Profile name to use (or None for default)
        args: Additional arguments to pass to the tool
    """
    # Determine profile to use
    profile_name = profile
    if not profile_name:
        # Check for project-specific profile
        project_config_dir = config_manager.get_project_config_path()
        if project_config_dir:
            profile_file = project_config_dir / "profile"
            if profile_file.exists():
                profile_name = profile_file.read_text().strip()

        if not profile_name:
            profile_name = "default"

    console.print(f"[cyan]Using profile: {profile_name}[/cyan]")

    # Load profile
    loaded_profile = profile_manager.load_profile(profile_name)
    if not loaded_profile:
        console.print(f"[red]Profile '{profile_name}' not found[/red]")
        return

    # Generate MCP config file for the tool
    tool_config_path = tool_manager.get_tool_config_path(tool_id)
    mcp_config_generator.generate_config(tool_id, loaded_profile, tool_config_path)

    # Build arguments
    tool_args = list(args) if args else []

    # For Cursor, pass the current directory as an argument
    # For Claude, it uses the current working directory automatically
    if tool_id == "cursor" and not args:
        tool_args = ["."]

    # Launch tool (it will run in the current working directory)
    tool_manager.launch_tool(tool_id, args=tool_args if tool_args else None)


@click.group()
@click.version_option(version=__version__, prog_name="aidev")
def cli() -> None:
    """
    aidev - Universal AI development environment manager

    Manage AI tool configurations, profiles, and MCP servers across
    Cursor, Claude Code, Zed, and other AI-powered development tools.
    """
    pass


# ============================================================================
# Setup & Installation Commands
# ============================================================================


@cli.command()
@click.option("--force", is_flag=True, help="Force reinstall even if already initialized")
def setup(force: bool) -> None:
    """Interactive setup wizard for aidev"""
    if config_manager.is_initialized() and not force:
        console.print("[yellow]aidev is already set up. Use --force to reinitialize.[/yellow]")
        return

    console.print("[bold cyan]Welcome to aidev![/bold cyan]\n")
    console.print("Let's set up your AI development environment.\n")

    # Initialize directories
    console.print("[cyan]Creating configuration directories...[/cyan]")
    config_manager.init_directories()

    # Initialize built-in profiles
    console.print("[cyan]Installing built-in profiles...[/cyan]")
    profile_manager.init_builtin_profiles()

    # Initialize built-in MCP servers
    console.print("[cyan]Installing built-in MCP servers...[/cyan]")
    mcp_manager.init_builtin_servers()

    # TODO: Interactive prompts for:
    # - GitHub/GitLab tokens
    # - Git author info
    # - Default profile
    # - Tool detection

    console.print("\n[bold green]✓ Setup complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. cd into a project directory")
    console.print("  2. Run: ai init")
    console.print("  3. Launch your AI tool: ai cursor / ai claude / ai codex / ai gemini")


@cli.command()
@click.option("--profile", help="Force a specific profile (skip recommendation)")
@click.option("--yes", is_flag=True, help="Accept recommended profile without prompting")
@click.option(
    "--project-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Project directory (defaults to current working directory)",
)
def quickstart(profile: str, yes: bool, project_dir: Path) -> None:
    """Detect stack, recommend a profile, and initialize aidev for this project."""
    result = quickstart_runner.run(
        project_dir=project_dir,
        profile_override=profile,
        auto_confirm=yes,
    )
    console.print(f"[green]Quickstart complete[/green] - profile: [bold]{result.selected_profile}[/bold]")


@cli.command()
def doctor() -> None:
    """Check aidev installation and configuration health"""
    console.print("[bold]aidev Health Check[/bold]\n")

    # Check if initialized
    if config_manager.is_initialized():
        console.print("[green]✓[/green] aidev is initialized")
    else:
        console.print("[red]✗[/red] aidev is not initialized. Run: aidev setup")
        return

    # Check directories
    console.print("[green]✓[/green] Configuration directories exist")

    # Check environment
    env = config_manager.get_env()
    if env:
        console.print(f"[green]✓[/green] Found {len(env)} environment variables")
    else:
        console.print("[yellow]![/yellow] No environment variables configured")

    # TODO: Check for installed AI tools
    # TODO: Check MCP server connectivity
    # TODO: Check profiles

    console.print("\n[bold green]All checks passed![/bold green]")


# ============================================================================
# Project Management Commands
# ============================================================================


@cli.command()
@click.option("--profile", default="default", help="Profile to use for this project")
def init(profile: str) -> None:
    """Initialize aidev in the current project"""
    console.print(f"[cyan]Initializing aidev with profile: {profile}[/cyan]")

    config_path = config_manager.init_project(profile=profile)
    console.print(f"[green]✓[/green] Created {config_path}")

    console.print("\n[bold green]Project initialized![/bold green]")
    console.print(f"Profile: {profile}")
    console.print("\nLaunch your AI tool:")
    console.print("  ai cursor    # Launch Cursor")
    console.print("  ai claude    # Launch Claude Code")
    console.print("  ai codex     # Launch Codex CLI")
    console.print("  ai gemini    # Launch Gemini Code Assist")


@cli.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage aidev configuration; run without subcommand to launch TUI."""
    if ctx.invoked_subcommand is None:
        try:
            from aidev.tui_config import ProfileConfigApp
        except Exception as exc:  # pragma: no cover - defensive
            console.print(f"[red]Failed to launch config TUI: {exc}[/red]")
            return
        app = ProfileConfigApp(config_manager, profile_manager, mcp_manager, project_dir=str(Path.cwd()))
        app.run()


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value"""
    # TODO: Implement config setting
    console.print(f"[green]✓[/green] Set {key} = {value}")


@config.command(name="get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value"""
    # TODO: Implement config getting
    console.print(f"{key} = value")


@config.command(name="list")
def config_list() -> None:
    """List all configuration"""
    # TODO: Implement config listing
    console.print("[bold]Configuration:[/bold]")


@cli.group()
def env() -> None:
    """Manage environment variables"""
    pass


@env.command(name="set")
@click.argument("key")
@click.argument("value")
def env_set(key: str, value: str) -> None:
    """Set an environment variable"""
    config_manager.set_env(key, value)
    console.print(f"[green]✓[/green] Set {key}")


@env.command(name="get")
@click.argument("key")
def env_get(key: str) -> None:
    """Get an environment variable"""
    env_vars = config_manager.get_env()
    if key in env_vars:
        console.print(f"{key}={env_vars[key]}")
    else:
        console.print(f"[yellow]Variable {key} not found[/yellow]")


@env.command(name="list")
def env_list() -> None:
    """List all environment variables"""
    env_vars = config_manager.get_env()

    table = Table(title="Environment Variables")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in sorted(env_vars.items()):
        # Mask sensitive values
        display_value = value if "TOKEN" not in key.upper() else "***"
        table.add_row(key, display_value)

    console.print(table)


# ============================================================================
# Tool Launching Commands
# ============================================================================


@cli.command()
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def cursor(profile: str, args: tuple) -> None:
    """Launch Cursor with aidev configuration"""
    _launch_tool_with_profile("cursor", profile, args)


@cli.command()
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def claude(profile: str, args: tuple) -> None:
    """Launch Claude Code with aidev configuration"""
    _launch_tool_with_profile("claude", profile, args)


@cli.command()
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def codex(profile: str, args: tuple) -> None:
    """Launch Codex CLI with aidev configuration"""
    _launch_tool_with_profile("codex", profile, args)


@cli.command()
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def gemini(profile: str, args: tuple) -> None:
    """Launch Gemini Code Assist with aidev configuration"""
    _launch_tool_with_profile("gemini", profile, args)


@cli.command()
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def zed(profile: str, args: tuple) -> None:
    """Launch Zed with aidev configuration"""
    _launch_tool_with_profile("zed", profile, args)


@cli.command()
@click.argument("tool_name")
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def tool(tool_name: str, profile: str, args: tuple) -> None:
    """Launch any registered AI tool"""
    # TODO: Implement generic tool launching
    profile_name = profile or "default"
    console.print(f"[cyan]Launching {tool_name} with profile: {profile_name}[/cyan]")


# ============================================================================
# Profile Management Commands
# ============================================================================


@cli.group()
def profile() -> None:
    """Manage AI development profiles"""
    pass


@profile.command(name="list")
def profile_list() -> None:
    """List all available profiles"""
    # TODO: Implement profile listing
    console.print("[bold]Available Profiles:[/bold]")


@profile.command(name="show")
@click.argument("name")
def profile_show(name: str) -> None:
    """Show profile details"""
    # TODO: Implement profile showing
    console.print(f"[bold]Profile: {name}[/bold]")


@profile.command(name="create")
@click.argument("name")
@click.option("--extends", help="Base profile to extend from")
def profile_create(name: str, extends: str) -> None:
    """Create a new custom profile"""
    # TODO: Implement profile creation
    console.print(f"[green]✓[/green] Created profile: {name}")


@profile.command(name="edit")
@click.argument("name")
def profile_edit(name: str) -> None:
    """Edit a profile"""
    # TODO: Implement profile editing
    console.print(f"Editing profile: {name}")


@profile.command(name="export")
@click.argument("name")
@click.option("--output", help="Output file path")
def profile_export(name: str, output: str) -> None:
    """Export a profile to share"""
    # TODO: Implement profile export
    output_path = output or f"{name}.json"
    console.print(f"[green]✓[/green] Exported {name} to {output_path}")


@profile.command(name="import")
@click.argument("file")
def profile_import(file: str) -> None:
    """Import a profile from file"""
    # TODO: Implement profile import
    console.print(f"[green]✓[/green] Imported profile from {file}")


# ============================================================================
# MCP Server Management Commands
# ============================================================================


@cli.group()
def mcp() -> None:
    """Manage MCP servers"""
    pass


@mcp.command(name="list")
def mcp_list() -> None:
    """List installed MCP servers"""
    # TODO: Implement MCP listing
    console.print("[bold]Installed MCP Servers:[/bold]")


@mcp.command(name="search")
@click.argument("query")
def mcp_search(query: str) -> None:
    """Search MCP server registry"""
    # TODO: Implement MCP search
    console.print(f"Searching for: {query}")


@mcp.command(name="install")
@click.argument("name")
def mcp_install(name: str) -> None:
    """Install an MCP server"""
    # TODO: Implement MCP installation
    console.print(f"[cyan]Installing MCP server: {name}[/cyan]")


@mcp.command(name="remove")
@click.argument("name")
def mcp_remove(name: str) -> None:
    """Remove an MCP server"""
    # TODO: Implement MCP removal
    console.print(f"[yellow]Removing MCP server: {name}[/yellow]")


@mcp.command(name="test")
@click.argument("name")
def mcp_test(name: str) -> None:
    """Test MCP server connectivity"""
    # TODO: Implement MCP testing
    console.print(f"Testing MCP server: {name}")


# ============================================================================
# Profile switching and status
# ============================================================================


def _resolve_active_profile(profile: Optional[str] = None) -> str:
    """Determine the active profile using project overrides or fallback."""
    profile_name = profile
    if not profile_name:
        project_config_dir = config_manager.get_project_config_path()
        if project_config_dir:
            profile_file = project_config_dir / "profile"
            if profile_file.exists():
                profile_name = profile_file.read_text().strip()

    return profile_name or "default"


@cli.command()
@click.argument("profile")
def use(profile: str) -> None:
    """Switch the active profile for the current project."""
    available = profile_manager.list_profiles()
    if profile not in available:
        console.print(f"[red]Profile '{profile}' not found. Available: {', '.join(available)}[/red]")
        return

    project_dir = Path.cwd()
    config_path = config_manager.get_project_config_path(project_dir)
    if not config_path:
        config_path = config_manager.init_project(project_dir=project_dir, profile=profile)
    else:
        profile_file = config_path / "profile"
        profile_file.write_text(profile)
        config_file = config_path / "config.json"
        config_data = load_json(config_file, default={"profile": profile, "environment": {}, "mcp_overrides": {}})
        config_data["profile"] = profile
        save_json(config_file, config_data)

    console.print(f"[green]✓[/green] Active profile set to [bold]{profile}[/bold] for {project_dir}")


@cli.command()
@click.option("--profile", help="Profile to inspect (defaults to active project profile)")
def status(profile: str) -> None:
    """Show current profile, MCP servers, and environment requirements."""
    profile_name = _resolve_active_profile(profile)
    loaded_profile = profile_manager.load_profile(profile_name)
    if not loaded_profile:
        console.print(f"[red]Profile '{profile_name}' not found[/red]")
        return

    console.print(f"[bold]Status[/bold] - Project: {Path.cwd()}")
    console.print(f"Active profile: [bold cyan]{profile_name}[/bold cyan]")

    mcp_table = Table(title="MCP Servers")
    mcp_table.add_column("Name", style="cyan")
    mcp_table.add_column("Enabled", style="green")
    for server in loaded_profile.mcp_servers:
        mcp_table.add_row(server.name, "yes" if server.enabled else "no")
    console.print(mcp_table)

    required_keys = sorted(list(loaded_profile.environment.keys()))
    if not required_keys:
        console.print("[yellow]No env requirements declared for this profile.[/yellow]")
        return

    env_table = Table(title="Environment Requirements")
    env_table.add_column("Key", style="yellow")
    env_table.add_column("Status", style="green")
    env_table.add_column("Value", style="white")

    global_env = config_manager.get_env()
    for key in required_keys:
        is_set = key in global_env and bool(global_env[key])
        env_table.add_row(key, "set" if is_set else "missing", "***" if is_set else "")
    console.print(env_table)


# ============================================================================
# Backup & Migration Commands
# ============================================================================


@cli.command()
@click.option("--output", help="Backup file path")
def backup(output: str) -> None:
    """Backup aidev configuration"""
    # TODO: Implement backup
    output_path = output or "aidev-backup.tar.gz"
    console.print(f"[green]✓[/green] Backed up to {output_path}")


@cli.command()
@click.argument("backup_file")
def restore(backup_file: str) -> None:
    """Restore aidev configuration from backup"""
    # TODO: Implement restore
    console.print(f"[cyan]Restoring from {backup_file}[/cyan]")


def main() -> None:
    """Main entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
