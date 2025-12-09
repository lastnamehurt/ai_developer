"""
CLI interface for aidev
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import json

import rich_click as click
from rich.console import Console
from rich.table import Table
from aidev import __version__
from aidev.config import ConfigManager
from aidev.tools import ToolManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.constants import ACTIVE_PROFILE_FILE
from aidev.quickstart import QuickstartRunner
from aidev.backup import BackupManager
from aidev.tutorial import Tutorial
from aidev.review import review_paths, staged_files, tracked_files
from aidev.utils import load_json, save_json, load_env, confirm
from aidev.errors import preflight
from aidev.workflow import WorkflowEngine
from aidev.env_requirements import (
    get_required_env_vars_for_profile,
    get_env_var_info,
    get_missing_env_vars,
    is_env_var_optional,
)

def _which_all(executable: str) -> list[str]:
    """Return all resolutions of an executable (best-effort, cross-shell)."""
    try:
        output = subprocess.check_output(["which", "-a", executable], text=True).strip()
        return [line for line in output.splitlines() if line]
    except Exception:
        resolved = shutil.which(executable)
        return [resolved] if resolved else []


def _pipx_bin_dir() -> Optional[str]:
    """Detect pipx bin dir if available."""
    if not shutil.which("pipx"):
        return None
    for args in (["pipx", "environment", "--value", "PIPX_BIN_DIR"], ["pipx", "environment"]):
        try:
            output = subprocess.check_output(args, text=True).strip()
        except Exception:
            continue
        if "PIPX_BIN_DIR=" in output:
            output = next((line.split("=", 1)[1] for line in output.splitlines() if line.startswith("PIPX_BIN_DIR=")), output)
        if output:
            return output.splitlines()[0]
    return None


def _ensure_pipx_installed(console: Console) -> bool:
    """Install pipx via pip --user if missing."""
    if shutil.which("pipx"):
        return True
    console.print("[yellow]![/yellow] pipx not found; installing via pip --user")
    result = subprocess.run(["python3", "-m", "pip", "install", "--user", "pipx"])
    if result.returncode != 0:
        console.print("[red]✗[/red] Failed to install pipx; please install pipx manually.")
        return False
    return True


def _fix_path_and_reinstall(console: Console) -> None:
    """Self-heal PATH and reinstall via pipx."""
    if not _ensure_pipx_installed(console):
        return
    subprocess.run(["pipx", "ensurepath"])
    console.print("[green]✓[/green] Ensured pipx shims are on PATH (restart shell if needed)")
    # Reinstall aidev into pipx to refresh shims
    result = subprocess.run(["pipx", "reinstall", "ai-developer", "--force"])
    if result.returncode == 0:
        console.print("[green]✓[/green] Reinstalled ai-developer via pipx")
    else:
        console.print("[yellow]![/yellow] pipx reinstall failed; trying install")
        install_result = subprocess.run(["pipx", "install", "--force", "ai-developer"])
        if install_result.returncode == 0:
            console.print("[green]✓[/green] Installed ai-developer via pipx")
        else:
            console.print("[red]✗[/red] pipx install/reinstall failed; check network and pipx configuration.")
    console.print("[dim]Tip: run `hash -r` in your shell to refresh command cache if needed.[/dim]")

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = False
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
click.rich_click.MAX_WIDTH = 100
click.rich_click.COMMAND_GROUPS = {
    "aidev.cli": [
        {
            "name": "Getting Started",
            "commands": ["quickstart", "setup", "init", "learn"],
        },
        {
            "name": "Profiles",
            "commands": ["profile", "use", "status"],
        },
        {
            "name": "MCP Servers",
            "commands": ["mcp"],
        },
        {
            "name": "Environment",
            "commands": ["env"],
        },
        {
            "name": "AI Tools",
            "commands": ["cursor", "claude", "codex", "gemini", "ollama", "aider", "tool", "review"],
        },
        {
            "name": "Utilities",
            "commands": ["config", "workflow", "doctor", "completion", "backup", "restore", "config-share"],
        },
    ]
}

console = Console()
config_manager = ConfigManager()
tool_manager = ToolManager()
profile_manager = ProfileManager()
mcp_manager = MCPManager()
mcp_config_generator = MCPConfigGenerator()
backup_manager = BackupManager()
quickstart_runner = QuickstartRunner(config_manager, profile_manager, mcp_manager)


# ============================================================================
# Helper Functions
# ============================================================================


def _launch_tool_with_profile(tool_id: str, profile: str, args: tuple) -> None:
    """
    Launch a tool with the specified profile and MCP configuration

    Args:
        tool_id: Tool identifier (cursor, claude, zed)
        profile: Profile name to use (or None to use active profile)
        args: Additional arguments to pass to the tool
    """
    # Ensure directories are initialized
    if not config_manager.is_initialized():
        config_manager.init_directories()

    # Determine profile to use
    profile_name = profile
    if not profile_name:
        # Check for active profile (globally set by user)
        if ACTIVE_PROFILE_FILE.exists():
            profile_name = ACTIVE_PROFILE_FILE.read_text().strip()

        # Fall back to project-specific profile
        if not profile_name:
            project_config_dir = config_manager.get_project_config_path()
            if project_config_dir:
                profile_file = project_config_dir / "profile"
                if profile_file.exists():
                    profile_name = profile_file.read_text().strip()

        # Fall back to default profile
        if not profile_name:
            profile_name = "default"
    else:
        # User specified a profile, save it as active
        ACTIVE_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        ACTIVE_PROFILE_FILE.write_text(profile_name)

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

    # MCP config is written directly to the tool's config location:
    # - Claude Code: .mcp.json (in current directory)
    # - Cursor: ~/.cursor/mcp.json
    # - Codex: ~/.codex/config.toml
    # - Gemini: ~/.gemini/settings.json
    # Tools read their respective MCP configs from these locations

    # Load environment variables to pass to the tool
    tool_env = config_manager.get_env()

    # Launch tool (it will run in the current working directory)
    tool_manager.launch_tool(tool_id, args=tool_args if tool_args else None, env=tool_env)


@click.group()
@click.version_option(version=__version__, prog_name="aidev")
def cli() -> None:
    """[bold cyan]aidev[/] - Universal AI development environment manager

    Manage AI tool configurations, profiles, and MCP servers across
    Cursor, Claude Code, Codex, Gemini, and other AI-powered development tools.

    [bold]Quick Examples:[/]

      [dim]# Auto-detect stack and setup[/]
      [green]ai quickstart[/]

      [dim]# Switch to web development profile[/]
      [green]ai use web[/]

      [dim]# Launch Cursor with infrastructure profile[/]
      [green]ai cursor --profile infra[/]

      [dim]# Find and install MCP servers[/]
      [green]ai mcp search postgres[/]
      [green]ai mcp install postgres[/]

      [dim]# Manage environment variables[/]
      [green]ai env set GITHUB_TOKEN ghp_xxx[/]

      [dim]# Check system health[/]
      [green]ai doctor[/]

    [bold]Documentation:[/] https://github.com/lastnamehurt/ai_developer
    """
    pass


# ============================================================================
# Setup & Installation Commands
# ============================================================================


def _prompt_for_env_var(env_var: str, encrypt: bool = False) -> Optional[str]:
    """
    Prompt user for a single environment variable with helpful context.

    Args:
        env_var: Environment variable name
        encrypt: Whether to encrypt the value

    Returns:
        The value entered by the user, or None if skipped
    """
    info = get_env_var_info(env_var)
    description = info.get("description", env_var)
    url = info.get("url")
    help_text = info.get("help", "")

    console.print(f"\n[bold cyan]{description}[/bold cyan]")
    if url:
        console.print(f"[dim]Get it at: {url}[/dim]")
    if help_text:
        console.print(f"[dim]Tip: {help_text}[/dim]")

    try:
        value = click.prompt("Enter value (or leave blank to skip)", default="", show_default=False)
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive mode or user interrupt
        console.print("[dim]Skipped (non-interactive or interrupted)[/dim]")
        return None

    if value.strip():
        if encrypt:
            console.print(f"[dim]✓ Value will be encrypted[/dim]")
        return value.strip()

    return None


def _setup_env_vars_for_profile(profile_name: str) -> None:
    """
    Prompt for and store required environment variables for a profile.

    Args:
        profile_name: Name of the profile being set up
    """
    profile = profile_manager.load_profile(profile_name)
    if not profile:
        console.print(f"[red]Could not load profile '{profile_name}'[/red]")
        return

    required_env_vars = get_required_env_vars_for_profile(profile)
    env_dict = config_manager.get_env()

    if not required_env_vars:
        console.print(f"\n[dim]✓ Profile '{profile_name}' has no required environment variables[/dim]")
        return

    # Check which are missing
    missing_vars = get_missing_env_vars(profile, env_dict.get)

    if not missing_vars:
        console.print(f"\n[green]✓ All required environment variables for '{profile_name}' are already set![/green]")
        return

    console.print(f"\n[bold yellow]Required Environment Variables for '{profile_name}' profile[/bold yellow]")
    console.print(f"[dim]{len(missing_vars)} of {len(required_env_vars)} required variables are missing:[/dim]\n")

    for env_var in missing_vars:
        info = get_env_var_info(env_var)
        should_encrypt = info.get("encrypt", False)

        if is_env_var_optional(env_var):
            if not confirm(f"Configure {env_var} (optional)?"):
                continue

        value = _prompt_for_env_var(env_var, encrypt=should_encrypt)
        if value:
            # Store the value (encrypted if needed)
            config_manager.set_env(env_var, value, project=False, encrypt=should_encrypt)

    console.print("\n[green]✓ Environment variables configured![/green]")


@cli.command()
@click.option("--force", is_flag=True, help="Force reinstall even if already initialized")
@click.option("--skip-env", is_flag=True, help="Skip environment variable setup")
def setup(force: bool, skip_env: bool) -> None:
    """Interactive setup wizard for aidev"""
    if config_manager.is_initialized() and not force:
        console.print("[yellow]aidev is already set up. Use --force to reinitialize.[/yellow]")
        if not skip_env and confirm("Configure missing environment variables?", default=False):
            console.print("\nWhich profile would you like to configure?")
            profiles = ["web", "infra"]
            for i, p in enumerate(profiles, 1):
                console.print(f"  {i}. {p}")
            try:
                choice = click.prompt("Select profile", type=click.Choice(["1", "2"]), default="1")
                profile_name = profiles[int(choice) - 1]
                _setup_env_vars_for_profile(profile_name)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Setup interrupted[/dim]")
        return

    console.print("[bold cyan]Welcome to aidev![/bold cyan]\n")
    console.print("Let's set up your AI development environment.\n")

    # Initialize directories
    console.print("[cyan]1/4 Creating configuration directories...[/cyan]")
    try:
        config_manager.init_directories()
        console.print("[green]✓ Directories created[/green]")
    except Exception as e:
        console.print(f"[red]Error creating directories: {e}[/red]")
        return

    # Initialize built-in profiles
    console.print("[cyan]2/4 Installing built-in profiles...[/cyan]")
    try:
        profile_manager.init_builtin_profiles()
        console.print("[green]✓ Profiles installed[/green]")
    except Exception as e:
        console.print(f"[red]Error installing profiles: {e}[/red]")
        return

    # Initialize built-in MCP servers
    console.print("[cyan]3/4 Installing built-in MCP servers...[/cyan]")
    try:
        mcp_manager.init_builtin_servers()
        console.print("[green]✓ MCP servers installed[/green]")
    except Exception as e:
        console.print(f"[red]Error installing MCP servers: {e}[/red]")
        return

    # Interactive setup for environment variables
    if not skip_env:
        console.print("\n[cyan]4/4 Setting up environment variables[/cyan]")
        console.print("[dim]These are needed for GitHub, GitLab, and other MCP servers.[/dim]")

        if confirm("Configure environment variables now?", default=True):
            console.print("\nWhich profile would you like to configure?")
            console.print("  1. [bold]web[/bold] (GitHub, general development)")
            console.print("  2. [bold]infra[/bold] (GitLab, Kubernetes, Atlassian)")
            console.print("  3. [bold]both[/bold]")
            console.print("  4. [bold]skip[/bold] (configure later with: ai env set KEY value)")

            try:
                choice = click.prompt(
                    "Select option",
                    type=click.Choice(["1", "2", "3", "4"]),
                    default="1",
                )

                profiles_to_setup = []
                if choice in ["1", "3"]:
                    profiles_to_setup.append("web")
                if choice in ["2", "3"]:
                    profiles_to_setup.append("infra")

                for profile_name in profiles_to_setup:
                    _setup_env_vars_for_profile(profile_name)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Setup interrupted[/dim]")

    console.print("\n[bold green]✓ Setup complete![/bold green]")
    console.print("\n[bold cyan]What's next:[/bold cyan]")
    console.print("  1. cd into a project directory")
    console.print("  2. Run: [bold]ai init[/bold] (or [bold]ai quickstart[/bold] for auto-detection)")
    console.print("  3. Launch your AI tool:")
    console.print("     • [bold]ai cursor[/bold] - Cursor editor")
    console.print("     • [bold]ai claude[/bold] - Claude Code")
    console.print("     • [bold]ai codex[/bold] - Codex CLI")
    console.print("     • [bold]ai gemini[/bold] - Gemini Code Assist")
    console.print("\n[dim]Missing env vars? Run: [bold]ai env set KEY value[/bold][/dim]")
    console.print("[dim]Check status: [bold]ai status[/bold][/dim]")


@cli.command()
def learn() -> None:
    """Interactive tutorial for learning aidev"""
    tutorial = Tutorial(config_manager, profile_manager, mcp_manager)
    tutorial.run()


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
@click.option(
    "--fix-path",
    is_flag=True,
    help="Ensure pipx shims are on PATH and reinstall ai-developer via pipx",
)
def doctor(fix_path: bool) -> None:
    """Check aidev installation and configuration health"""
    console.print("[bold]aidev Health Check[/bold]\n")

    # Check if initialized
    if config_manager.is_initialized():
        console.print("[green]✓[/green] aidev is initialized")
    else:
        console.print("[red]✗[/red] aidev is not initialized. Run: aidev setup")
        return

    console.print("[cyan]Running preflight checks...[/cyan]")
    env_keys = ["AIDEV_DEFAULT_PROFILE"]
    binaries = ["git"]
    env_lookup = lambda key: config_manager.get_env().get(key)
    all_ok = preflight(env_keys, binaries, env_lookup)

    # Check environment variables for active profile
    console.print("\n[cyan]Checking active profile environment variables...[/cyan]")
    current_profile_name = config_manager.get_current_profile()
    profile = profile_manager.load_profile(current_profile_name)

    if profile:
        missing = get_missing_env_vars(profile, env_lookup)
        if missing:
            console.print(f"[yellow]![/yellow] Profile '[bold]{current_profile_name}[/bold]' has {len(missing)} missing env vars:")
            for var in missing:
                if not is_env_var_optional(var):
                    info = get_env_var_info(var)
                    url_hint = f" (get at: {info.get('url')})" if info.get('url') else ""
                    console.print(f"   [red]✗[/red] {var}{url_hint}")
                    all_ok = False
            console.print(f"[dim]Set them with: ai env set KEY value[/dim]")
        else:
            console.print(f"[green]✓[/green] All required env vars for '{current_profile_name}' are set")
    else:
        console.print(f"[yellow]![/yellow] Could not load profile '{current_profile_name}'")
        all_ok = False

    console.print("\n[cyan]PATH & shim checks...[/cyan]")
    ai_locations = _which_all("ai")
    pipx_bin = _pipx_bin_dir()
    if ai_locations:
        console.print(f"[green]✓[/green] ai resolves to {ai_locations[0]}")
        if pipx_bin and not ai_locations[0].startswith(pipx_bin):
            console.print(f"[yellow]![/yellow] ai is not from pipx (expected under {pipx_bin}).")
            console.print("[dim]Hint: run `pipx reinstall ai-developer --force` or use --fix-path.[/dim]")
        if any("/venv/" in loc or "/.venv/" in loc for loc in ai_locations):
            console.print("[yellow]![/yellow] Detected ai inside a virtualenv; it may shadow the pipx shim.")
        if len(ai_locations) > 1:
            console.print(f"[dim]All ai locations: {', '.join(ai_locations)}[/dim]")
    else:
        console.print("[red]✗[/red] ai not found on PATH. Run with --fix-path or ensure pipx shims are exported.")
        all_ok = False

    if fix_path:
        console.print("\n[cyan]Applying pipx path fix...[/cyan]")
        _fix_path_and_reinstall(console)

    if all_ok and (ai_locations or fix_path):
        console.print("\n[bold green]All checks passed![/bold green]")
    else:
        console.print("\n[bold yellow]Fix the above items and re-run ai doctor.[/bold yellow]")


@cli.command()
@click.argument("workflow_name", required=False)
@click.argument("input_value", required=False)
@click.option("--ticket", help="Ticket key, URL, or org/repo#123")
@click.option("--file", "ticket_file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Load ticket text from file")
@click.option("--tool", "tool_override", help="Force assistant/tool to use (e.g., claude, codex)")
@click.option("--list", "list_only", is_flag=True, help="List available workflows")
@click.option("--from-step", "from_step", help="Start execution from this step name")
@click.option("--step-only", is_flag=True, help="Run only the selected step")
@click.option("--output", "output_mode", type=click.Choice(["table", "json"], case_sensitive=False), default="table", help="Output format for run manifest")
@click.option("--handoff/--no-handoff", default=True, help="Launch assistant with manifest for interactive execution (default: on)")
@click.option("--execute", is_flag=True, help="Run steps headless before handoff")
def workflow(workflow_name: Optional[str], input_value: Optional[str], ticket: Optional[str], ticket_file: Optional[Path], tool_override: Optional[str], list_only: bool, from_step: Optional[str], step_only: bool, output_mode: str, handoff: bool, execute: bool) -> None:
    """Run or list workflows defined in .aidev/workflows.yaml. Input can be passed via --ticket/--file or as a positional value (ticket key or file path)."""
    engine = WorkflowEngine(project_dir=Path.cwd())
    workflows, warnings = engine.load_workflows()

    if not workflows:
        console.print("[red]✗[/red] No workflows defined. Edit .aidev/workflows.yaml to add one.")
        return
    if warnings:
        console.print("[yellow]![/yellow] Workflow schema warnings:")
        for w in warnings:
            console.print(f"  - {w}")

    # Support "list" as a workflow name to trigger listing (for convenience)
    if workflow_name == "list" and not list_only:
        list_only = True
    
    # Support "status" as a subcommand
    if workflow_name == "status":
        # Use input_value as manifest_file if provided
        manifest_file = input_value if input_value else None
        engine = WorkflowEngine(project_dir=Path.cwd())
        runs_dir = engine.runs_dir()
        
        if not runs_dir.exists():
            console.print("[red]✗[/red] No workflow runs directory found.")
            return
        
        if manifest_file:
            # User provided a manifest file name or path
            manifest_path = Path(manifest_file)
            if not manifest_path.is_absolute():
                # Try relative to runs directory first
                manifest_path = runs_dir / manifest_file
                if not manifest_path.exists():
                    # Try as full path
                    manifest_path = Path(manifest_file)
        else:
            # Find the most recent manifest
            manifests = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not manifests:
                console.print("[red]✗[/red] No workflow runs found.")
                return
            manifest_path = manifests[0]
        
        if not manifest_path.exists():
            console.print(f"[red]✗[/red] Manifest file not found: {manifest_path}")
            return
        
        engine.check_workflow_status(manifest_path)
        return
    
    # Support "mark-complete" as a subcommand
    if workflow_name == "mark-complete":
        # Use input_value as manifest_file if provided
        manifest_file = input_value if input_value else None
        engine = WorkflowEngine(project_dir=Path.cwd())
        runs_dir = engine.runs_dir()
        
        if not runs_dir.exists():
            console.print("[red]✗[/red] No workflow runs directory found.")
            return
        
        if manifest_file:
            # User provided a manifest file name or path
            manifest_path = Path(manifest_file)
            if not manifest_path.is_absolute():
                # Try relative to runs directory first
                manifest_path = runs_dir / manifest_file
                if not manifest_path.exists():
                    # Try as full path
                    manifest_path = Path(manifest_file)
        else:
            # Find the most recent manifest
            manifests = sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not manifests:
                console.print("[red]✗[/red] No workflow runs found.")
                return
            manifest_path = manifests[0]
        
        if not manifest_path.exists():
            console.print(f"[red]✗[/red] Manifest file not found: {manifest_path}")
            return
        
        engine.mark_steps_complete(manifest_path)
        return

    if list_only:
        table = Table(title="Available Workflows", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white", overflow="fold")
        
        for name, spec in sorted(workflows.items()):
            table.add_row(name, spec.description)
        
        console.print(table)
        return

    # Interpret positional input if provided: prefer file if path exists, else treat as free-form prompt
    user_prompt = None
    if input_value and not ticket and not ticket_file:
        candidate_path = Path(input_value)
        if candidate_path.exists():
            ticket_file = candidate_path
        else:
            user_prompt = input_value

    selected_name = workflow_name or ("implement_ticket" if "implement_ticket" in workflows else next(iter(workflows)))
    if selected_name not in workflows:
        console.print(f"[red]✗[/red] Workflow '{selected_name}' not found. Use --list to see options.")
        return

    spec = workflows[selected_name]
    if ticket_file and not spec.allow_file:
        console.print(f"[red]✗[/red] Workflow '{selected_name}' does not allow --file input.")
        return

    project_config = config_manager.get_project_config_path(Path.cwd())
    project_default_assistant = None
    if project_config:
        cfg_file = project_config / "config.json"
        if cfg_file.exists():
            try:
                project_default_assistant = load_json(cfg_file, default={}).get("default_assistant")
            except Exception:
                project_default_assistant = None

    run_path = engine.run_workflow(
        spec,
        ticket=ticket,
        ticket_file=ticket_file,
        user_prompt=user_prompt,
        tool_override=tool_override,
        project_default_assistant=project_default_assistant,
        from_step=from_step,
        step_only=step_only,
    )
    if execute:
        run_path = engine.execute_manifest(run_path)
    if output_mode == "json":
        console.print(Path(run_path).read_text())
    else:
        console.print(f"[cyan]Run manifest saved to[/cyan] {run_path}")

    if handoff:
        engine.handoff_to_assistant(run_path, tool_override or spec.tool_default or engine.resolver._fallback_by_availability())


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False))
def completion(shell: str) -> None:
    """Generate shell completion script

    \b
    Examples:
      # Bash
      ai completion bash >> ~/.bashrc
      # Or for current session:
      eval "$(ai completion bash)"

      # Zsh
      ai completion zsh >> ~/.zshrc
      # Or for current session:
      eval "$(ai completion zsh)"

      # Fish
      ai completion fish > ~/.config/fish/completions/ai.fish
    """
    import subprocess
    import sys

    shell_lower = shell.lower()

    if shell_lower == "bash":
        script = '''
_ai_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _AI_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

complete -o nosort -F _ai_completion ai
complete -o nosort -F _ai_completion aidev
'''
        print(script)

    elif shell_lower == "zsh":
        script = '''
#compdef ai aidev

_ai_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[ai] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _AI_COMPLETE=zsh_complete ai)}")

    for type_value in $response; do
        completions+=("${type_value#*,}")
    done

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _ai_completion ai
compdef _ai_completion aidev
'''
        print(script)

    elif shell_lower == "fish":
        script = '''
function _ai_completion
    set -l response (env _AI_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) ai)

    for completion in $response
        set -l metadata (string split "," -- $completion)

        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete --no-files --command ai --arguments "(_ai_completion)"
complete --no-files --command aidev --arguments "(_ai_completion)"
'''
        print(script)


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
@click.option("--project", is_flag=True, help="Set for current project only")
@click.option("--encrypt", is_flag=True, help="Encrypt the value before storing")
def env_set(key: str, value: str, project: bool, encrypt: bool) -> None:
    """Set an environment variable (global by default, project with --project)."""
    config_manager.set_env(key, value, project=project, encrypt=encrypt)
    scope = "project" if project else "global"
    suffix = " (encrypted)" if encrypt else ""
    console.print(f"[green]✓[/green] Set {key} ({scope}){suffix}")


@env.command(name="get")
@click.argument("key")
@click.option("--project", is_flag=True, help="Read from current project first")
def env_get(key: str, project: bool) -> None:
    """Get an environment variable"""
    env_vars = config_manager.get_env(project_dir=Path.cwd() if project else None)
    if key in env_vars:
        console.print(f"{key}={env_vars[key]}")
    else:
        console.print(f"[yellow]Variable {key} not found[/yellow]")


@env.command(name="list")
@click.option("--project", is_flag=True, help="Show merged env with project overrides")
def env_list(project: bool) -> None:
    """List all environment variables (merged global + project)."""
    env_vars = config_manager.get_env(project_dir=Path.cwd() if project else None)

    table = Table(title="Environment Variables")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Scope", style="yellow")

    # Load raw scopes for display
    from aidev.utils import load_env
    from aidev.constants import ENV_FILE

    global_env_raw = load_env(ENV_FILE)
    project_env_path = Path.cwd() / ".aidev" / ".env"
    project_env_raw = load_env(project_env_path) if project_env_path.exists() else {}

    for key, value in sorted(env_vars.items()):
        raw_value = project_env_raw.get(key) if key in project_env_raw else global_env_raw.get(key, "")
        is_encrypted = raw_value.startswith("ENC::")
        display_value = "***" if is_encrypted or any(secret in key.upper() for secret in ["TOKEN", "KEY", "SECRET"]) else value
        scope = "project" if key in project_env_raw else "global"
        table.add_row(key, display_value, scope)

    console.print(table)


@env.command(name="unlock")
def env_unlock() -> None:
    """Ensure the encryption key exists and is ready for decrypting secrets."""
    from aidev.secrets import unlock_env_key

    key_path = unlock_env_key()
    console.print(f"[green]✓[/green] Env key ready at {key_path}")


@env.command(name="validate")
@click.option("--profile", help="Profile to validate against (defaults to active)")
def env_validate(profile: str) -> None:
    """Validate environment against profile requirements."""
    profile_name = profile or _resolve_active_profile()
    loaded_profile = profile_manager.load_profile(profile_name)
    if not loaded_profile:
        return
    env_vars = config_manager.get_env(project_dir=Path.cwd())
    required_keys = sorted(list(loaded_profile.environment.keys()))
    missing = [k for k in required_keys if not env_vars.get(k)]
    unused = [k for k in env_vars.keys() if k not in required_keys]

    if missing:
        console.print("[red]Missing required env keys:[/red]")
        for key in missing:
            console.print(f"  - {key} (set with: ai env set {key} <value>)")
    else:
        console.print("[green]All required env keys are set.[/green]")

    if unused:
        console.print("[yellow]Unused env keys (not declared in profile):[/yellow]")
        for key in unused:
            console.print(f"  - {key}")


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
def ollama(profile: str, args: tuple) -> None:
    """Launch Ollama with aidev configuration"""
    _launch_tool_with_profile("ollama", profile, args)


@cli.command()
@click.option("--profile", default="aider", help="Profile to use (default: aider)")
@click.option("--model", help="Model to use (e.g., claude-sonnet-4-5, ollama/codellama)")
@click.option("--yes", is_flag=True, help="Auto-accept changes")
@click.argument("args", nargs=-1)
def aider(profile: str, model: str, yes: bool, args: tuple) -> None:
    """Launch Aider AI pair programming tool with aidev configuration
    
    Examples:
      ai aider                                    # Launch with aider profile
      ai aider --model claude-sonnet-4-5         # Use Claude model
      ai aider --model ollama/codellama          # Use local Ollama model
      ai aider --yes                              # Auto-accept changes
      ai aider --profile web                      # Use web profile instead
    """
    # Use aider profile by default if not specified
    profile_name = profile or "aider"
    
    # Ensure directories are initialized
    if not config_manager.is_initialized():
        config_manager.init_directories()
    
    # Determine profile to use
    if not profile_name:
        # Check for active profile
        if ACTIVE_PROFILE_FILE.exists():
            profile_name = ACTIVE_PROFILE_FILE.read_text().strip()
        # Fall back to project-specific profile
        if not profile_name:
            project_config_dir = config_manager.get_project_config_path()
            if project_config_dir:
                profile_file = project_config_dir / "profile"
                if profile_file.exists():
                    profile_name = profile_file.read_text().strip()
        # Fall back to aider profile
        if not profile_name:
            profile_name = "aider"
    
    console.print(f"[cyan]Using profile: {profile_name}[/cyan]")
    
    # Load profile
    loaded_profile = profile_manager.load_profile(profile_name)
    if not loaded_profile:
        console.print(f"[yellow]Profile '{profile_name}' not found, using default[/yellow]")
        loaded_profile = profile_manager.load_profile("default")
        if not loaded_profile:
            console.print("[red]No profiles available. Run 'ai setup' first.[/red]")
            return
    
    # Load environment variables to pass to Aider
    tool_env = config_manager.get_env()
    
    # Build Aider arguments (tool_manager will prepend the binary name)
    aider_args = []
    
    # Add model if specified
    if model:
        aider_args.extend(["--model", model])
    
    # Add auto-accept flag
    if yes:
        aider_args.append("--yes")
    
    # Add any additional arguments
    if args:
        aider_args.extend(args)
    
    # Launch Aider
    try:
        tool_manager.launch_tool("aider", args=aider_args if aider_args else None, env=tool_env)
    except Exception as e:
        console.print(f"[red]Failed to launch Aider: {e}[/red]")
        console.print("[yellow]Make sure Aider is installed: pip install aider-chat[/yellow]")


@cli.command()
@click.argument("tool_name")
@click.option("--profile", help="Profile to use")
@click.argument("args", nargs=-1)
def tool(tool_name: str, profile: str, args: tuple) -> None:
    """Launch any registered AI tool"""
    # TODO: Implement generic tool launching
    profile_name = profile or "default"
    console.print(f"[cyan]Launching {tool_name} with profile: {profile_name}[/cyan]")

@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--all", "all_files", is_flag=True, help="Review all tracked files.")
@click.option("--staged", is_flag=True, help="Review staged files.")
@click.option("--provider", type=click.Choice(["heuristic", "external", "ollama"]), help="Choose review provider")
@click.option(
    "--review-config",
    type=click.Path(exists=True),
    help="Path to review config (default: ~/.aidev/review.json).",
)
def review(files: tuple[str], all_files: bool, staged: bool, provider: str, review_config: str) -> None:
    """Run a lightweight local code review (heuristics by default; external if configured)."""
    target_paths: list[Path] = []
    if files:
        target_paths = [Path(f) for f in files]
    elif staged:
        target_paths = staged_files()
        if not target_paths:
            console.print("[yellow]No staged files to review.[/yellow]")
            return
    elif all_files:
        target_paths = tracked_files()
        if not target_paths:
            console.print("[yellow]No tracked files to review.[/yellow]")
            return
    else:
        # Default to staged if nothing specified
        target_paths = staged_files()
        if not target_paths:
            console.print("[yellow]No staged files to review. Use --all or pass files.[/yellow]")
            return

    from aidev.review import load_review_config, external_review, ReviewConfig, ollama_review

    cfg: ReviewConfig = load_review_config(Path(review_config)) if review_config else load_review_config()
    if provider:
        cfg.provider = provider

    if cfg.provider == "external":
        if not cfg.command:
            console.print("[red]External reviewer selected but no command configured (review.json -> command).[/red]")
            return
        console.print(f"[cyan]Using external reviewer: {' '.join(cfg.command)}[/cyan]")
        comments = external_review(target_paths, cfg.command)
    elif cfg.provider == "ollama":
        console.print(f"[cyan]Using ollama reviewer: model={cfg.ollama_model}[/cyan]")
        comments = ollama_review(target_paths, cfg.ollama_model, cfg.ollama_prompt)
    else:
        comments = review_paths(target_paths)
    if comments:
        console.print("\n[bold red]Review Findings:[/bold red]")
        for c in comments:
            console.print(f"  [yellow]{c.file_path}:{c.line}[/yellow] [{c.severity}] {c.message}")
    else:
        console.print("\n[bold green]✓ No findings.[/bold green]")


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
    from aidev.constants import BUILTIN_PROFILES

    profiles = profile_manager.list_profiles()

    if not profiles:
        console.print("[yellow]No profiles found. Run 'ai setup' to initialize.[/yellow]")
        return

    table = Table(title="Available Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Description", style="white")

    for name in profiles:
        profile_type = "built-in" if name in BUILTIN_PROFILES else "custom"
        # Load profile to get description
        loaded = profile_manager.load_profile(name)
        description = loaded.description if loaded else ""
        table.add_row(name, profile_type, description)

    console.print(table)


@profile.command(name="show")
@click.argument("name")
def profile_show(name: str) -> None:
    """Show profile details"""
    from aidev.constants import BUILTIN_PROFILES

    loaded = profile_manager.load_profile(name)
    if not loaded:
        return

    # Header
    profile_type = "built-in" if name in BUILTIN_PROFILES else "custom"
    console.print(f"\n[bold cyan]{name}[/bold cyan] [dim]({profile_type})[/dim]")
    console.print(f"[dim]{loaded.description}[/dim]\n")

    # MCP Servers
    if loaded.mcp_servers:
        mcp_table = Table(title="MCP Servers", show_header=True)
        mcp_table.add_column("Name", style="cyan")
        mcp_table.add_column("Enabled", style="green")

        for server in loaded.mcp_servers:
            status = "✓" if server.enabled else "✗"
            mcp_table.add_row(server.name, status)

        console.print(mcp_table)
    else:
        console.print("[dim]No MCP servers configured[/dim]")

    # Environment Variables
    if loaded.environment:
        console.print(f"\n[bold]Environment Variables:[/bold]")
        for key, value in loaded.environment.items():
            console.print(f"  [yellow]{key}[/yellow] = [dim]{value}[/dim]")
    else:
        console.print("\n[dim]No environment variables configured[/dim]")

    # Tags
    if loaded.tags:
        console.print(f"\n[bold]Tags:[/bold] {', '.join(loaded.tags)}")

    # Inheritance
    if loaded.extends:
        console.print(f"\n[dim]Extends:[/dim] {loaded.extends}")

    console.print()


@profile.command(name="create")
@click.argument("name")
@click.option("--extends", help="Base profile to extend from")
def profile_create(name: str, extends: str) -> None:
    """Create a new custom profile"""
    # TODO: Implement profile creation
    console.print(f"[green]✓[/green] Created profile: {name}")


@profile.command(name="clone")
@click.argument("source")
@click.argument("target")
@click.option("--description", "-d", help="Custom description for cloned profile")
@click.option(
    "--mcp-servers",
    "-m",
    help="Comma-separated list of MCP servers to use (overrides source)",
)
def profile_clone(source: str, target: str, description: str, mcp_servers: str) -> None:
    """Clone an existing profile

    \b
    Examples:
      # Clone web profile to my-web
      ai profile clone web my-web

      # Clone with custom description
      ai profile clone web my-web -d "My custom web profile"

      # Clone with specific MCP servers
      ai profile clone infra k8s-only -m kubernetes,docker,git
    """
    # Parse MCP servers if provided
    mcp_list = None
    if mcp_servers:
        mcp_list = [s.strip() for s in mcp_servers.split(",")]

    # Clone the profile
    cloned = profile_manager.clone_profile(
        source_name=source,
        target_name=target,
        description=description,
        mcp_servers=mcp_list,
    )

    if cloned:
        # Show what was cloned
        console.print(f"\n[bold]Cloned Profile:[/bold] [cyan]{target}[/cyan]")
        console.print(f"[dim]Description:[/dim] {cloned.description}")
        console.print(f"[dim]MCP Servers:[/dim] {len(cloned.mcp_servers)} configured")

        # Suggest next steps
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  • Edit: [cyan]ai config[/cyan] (then select '{target}')")
        console.print(f"  • Use:  [cyan]ai use {target}[/cyan]")


@profile.command(name="diff")
@click.argument("profile1")
@click.argument("profile2")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def profile_diff(profile1: str, profile2: str, json_output: bool) -> None:
    """Compare two profiles and show differences

    \b
    Examples:
      # Compare web and infra profiles
      ai profile diff web infra

      # Output as JSON for scripting
      ai profile diff web infra --json
    """
    import json as json_module
    from rich.panel import Panel

    # Get differences
    diff = profile_manager.diff_profiles(profile1, profile2)
    if not diff:
        return

    # JSON output
    if json_output:
        console.print(json_module.dumps(diff, indent=2))
        return

    # Human-readable output
    console.print(f"\n[bold]Comparing:[/bold] [cyan]{profile1}[/cyan] → [cyan]{profile2}[/cyan]\n")

    # MCP Servers diff
    console.print("[bold]MCP Servers:[/bold]")
    mcp = diff["mcp_servers"]
    if mcp["added"]:
        for server in mcp["added"]:
            console.print(f"  [green]+[/green] {server} (added in {profile2})")
    if mcp["removed"]:
        for server in mcp["removed"]:
            console.print(f"  [red]-[/red] {server} (only in {profile1})")
    if mcp["common"]:
        for server in mcp["common"]:
            console.print(f"  [dim]=[/dim] {server} (common)")
    if not mcp["added"] and not mcp["removed"] and not mcp["common"]:
        console.print("  [dim](no MCP servers configured)[/dim]")

    # Environment variables diff
    console.print(f"\n[bold]Environment Variables:[/bold]")
    env = diff["environment"]
    if env["added"]:
        for var in env["added"]:
            console.print(f"  [green]+[/green] {var} (added in {profile2})")
    if env["removed"]:
        for var in env["removed"]:
            console.print(f"  [red]-[/red] {var} (only in {profile1})")
    if env["changed"]:
        for var, values in env["changed"].items():
            console.print(
                f"  [yellow]±[/yellow] {var}: [dim]{values['from']}[/dim] → {values['to']}"
            )
    if env["common"] and not env["changed"]:
        for var in env["common"]:
            console.print(f"  [dim]=[/dim] {var} (common, same value)")
    if not env["added"] and not env["removed"] and not env["changed"] and not env["common"]:
        console.print("  [dim](no environment variables)[/dim]")

    # Tags diff
    console.print(f"\n[bold]Tags:[/bold]")
    tags = diff["tags"]
    if tags["added"]:
        for tag in tags["added"]:
            console.print(f"  [green]+[/green] {tag}")
    if tags["removed"]:
        for tag in tags["removed"]:
            console.print(f"  [red]-[/red] {tag}")
    if tags["common"]:
        for tag in tags["common"]:
            console.print(f"  [dim]=[/dim] {tag}")
    if not tags["added"] and not tags["removed"] and not tags["common"]:
        console.print("  [dim](no tags)[/dim]")

    console.print()


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
    """Export a profile to share

    \b
    Examples:
      # Export with default filename
      ai profile export web

      # Export with custom filename
      ai profile export web --output my-web-profile.json
    """
    output_path = Path(output) if output else Path(f"{name}.json")
    if profile_manager.export_profile(name, output_path):
        console.print(f"[green]✓[/green] Exported profile '[cyan]{name}[/cyan]' to {output_path}")
        console.print("[dim]Share this file with your team![/dim]")


@profile.command(name="import")
@click.argument("file")
def profile_import(file: str) -> None:
    """Import a profile from file

    \b
    Examples:
      # Import a shared profile
      ai profile import team-profile.json
    """
    input_path = Path(file)
    imported = profile_manager.import_profile(input_path)
    if imported:
        console.print(f"[green]✓[/green] Imported profile '[cyan]{imported.name}[/cyan]'")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  • View:  [cyan]ai profile show {imported.name}[/cyan]")
        console.print(f"  • Use:   [cyan]ai use {imported.name}[/cyan]")


@profile.command(name="templates")
@click.argument("template_name", required=False)
@click.argument("profile_name", required=False)
def profile_templates(template_name: str, profile_name: str) -> None:
    """Browse and create profiles from pre-built templates

    \b
    Examples:
      # List all templates
      ai profile templates

      # Create profile from template
      ai profile templates nextjs-fullstack my-project
      ai profile templates django-api backend-api
    """
    # If no arguments, list all templates
    if not template_name:
        templates = profile_manager.get_profile_templates()

        table = Table(title="Profile Templates", show_header=True)
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Base", style="yellow")
        table.add_column("Tags", style="dim")

        for template in templates:
            tags = ", ".join(template["tags"][:3])  # Show first 3 tags
            if len(template["tags"]) > 3:
                tags += "..."
            table.add_row(
                template["name"],
                template["description"],
                template["base"],
                tags,
            )

        console.print(table)
        console.print("\n[bold]Usage:[/bold]")
        console.print("  ai profile templates <template-name> <new-profile-name>")
        console.print("\n[bold]Example:[/bold]")
        console.print("  ai profile templates nextjs-fullstack my-project")
        return

    # Create profile from template
    if not profile_name:
        console.print("[red]Error: Please provide a profile name[/red]")
        console.print("Usage: ai profile templates <template-name> <new-profile-name>")
        return

    created = profile_manager.create_from_template(template_name, profile_name)

    if created:
        # Show what was created
        console.print(f"\n[bold]Created Profile:[/bold] [cyan]{profile_name}[/cyan]")
        console.print(f"[dim]Template:[/dim] {template_name}")
        console.print(f"[dim]Description:[/dim] {created.description}")
        console.print(f"[dim]MCP Servers:[/dim] {len(created.mcp_servers)} configured")

        # Suggest next steps
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  • View:  [cyan]ai profile show {profile_name}[/cyan]")
        console.print(f"  • Edit:  [cyan]ai config[/cyan] (then select '{profile_name}')")
        console.print(f"  • Use:   [cyan]ai use {profile_name}[/cyan]")


# ============================================================================
# MCP Server Management Commands
# ============================================================================


@cli.group()
def mcp() -> None:
    """Manage MCP servers"""
    pass


@mcp.command(name="list")
def mcp_list() -> None:
    """List installed MCP servers."""
    installed = mcp_manager.list_installed()
    if not installed:
        console.print("[yellow]No MCP servers installed.[/yellow]")
        return
    table = Table(title="Installed MCP Servers")
    table.add_column("Name", style="cyan")
    for name in installed:
        table.add_row(name)
    console.print(table)


@mcp.command(name="search")
@click.argument("query", required=False, default="")
@click.option("--refresh", is_flag=True, help="Refresh registry cache")
def mcp_search(query: str, refresh: bool) -> None:
    """Search MCP server registry."""
    registry = mcp_manager.fetch_registry(force=refresh)
    if query:
        registry = [r for r in registry if query.lower() in r.name.lower() or query.lower() in r.description.lower()]
    if not registry:
        console.print("[yellow]No registry entries found.[/yellow]")
        return

    table = Table(title="Registry")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Version", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Profiles", style="magenta")
    for entry in registry:
        tags = ", ".join(entry.tags) if entry.tags else "-"
        profiles = ", ".join(entry.compatible_profiles) if entry.compatible_profiles else "-"
        table.add_row(entry.name, entry.description, entry.version, tags, profiles)
    console.print(table)


@mcp.command(name="browse")
@click.option("--refresh", is_flag=True, help="Refresh registry cache before launching")
def mcp_browse(refresh: bool) -> None:
    """Launch a TUI to browse and install MCP servers."""
    try:
        from aidev.tui_mcp_browser import MCPBrowserApp
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Failed to launch MCP browser: {exc}[/red]")
        return
    app = MCPBrowserApp(mcp_manager=mcp_manager, refresh_on_start=refresh)
    app.run()


@mcp.command(name="install")
@click.argument("name")
@click.option("--profile", help="Profile to enable this server in")
def mcp_install(name: str, profile: str) -> None:
    """Install an MCP server and optionally enable it in a profile."""
    ok = mcp_manager.install_server(name)
    if not ok:
        return
    target_profile = profile or _resolve_active_profile()
    loaded_profile = profile_manager.load_profile(target_profile)
    if loaded_profile:
        if name not in [s.name for s in loaded_profile.mcp_servers]:
            loaded_profile.mcp_servers.append(MCPServerConfig(name=name, enabled=True))
            profile_manager.save_profile(loaded_profile, custom=True)
            console.print(f"[green]✓[/green] Enabled '{name}' in profile '{target_profile}'")


@mcp.command(name="remove")
@click.argument("name")
def mcp_remove(name: str) -> None:
    """Remove an MCP server."""
    removed = mcp_manager.remove_server(name, profile_manager=profile_manager)
    if not removed:
        return
    console.print(f"[yellow]Removed MCP server: {name}[/yellow]")


@mcp.command(name="test")
@click.argument("name")
def mcp_test(name: str) -> None:
    """Test MCP server connectivity."""
    if mcp_manager.test_server(name):
        console.print(f"[green]✓[/green] {name} responded")
    else:
        console.print(f"[red]✗[/red] {name} failed connectivity")


# ============================================================================
# Profile switching and status
# ============================================================================


def _resolve_active_profile(profile: Optional[str] = None) -> str:
    """Determine the active profile using project overrides or fallback."""
    if profile:
        return profile
    return config_manager.get_current_profile(project_dir=Path.cwd())


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
    """Create backup of aidev configuration

    \b
    Examples:
      # Auto-generate backup filename
      ai backup

      # Custom output path
      ai backup --output my-backup.tar.gz
    """
    output_path = Path(output) if output else None
    backup_manager.create_backup(output_path)


@cli.command()
@click.argument("backup_file")
@click.option("--force", is_flag=True, help="Force restore without confirmation")
def restore(backup_file: str, force: bool) -> None:
    """Restore aidev configuration from backup

    \b
    Examples:
      # Restore with confirmation
      ai restore aidev-backup-macbook-20231206.tar.gz

      # Force restore without prompting
      ai restore backup.tar.gz --force
    """
    backup_path = Path(backup_file)
    backup_manager.restore_backup(backup_path, force=force)


@cli.group(name="config-share")
def config_share() -> None:
    """Share configurations with team (export/import without secrets)"""
    pass


@config_share.command(name="export")
@click.option("--output", required=True, help="Output file path")
def config_export(output: str) -> None:
    """Export configuration for sharing (without secrets)

    \b
    Examples:
      # Export for team sharing
      ai config-share export --output team-config.json
    """
    output_path = Path(output)
    backup_manager.export_config(output_path)


@config_share.command(name="import")
@click.argument("config_file")
def config_import(config_file: str) -> None:
    """Import shared configuration

    \b
    Examples:
      # Import team configuration
      ai config-share import team-config.json
    """
    config_path = Path(config_file)
    backup_manager.import_config(config_path)


def main() -> None:
    """Main entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
