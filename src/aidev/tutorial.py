"""
Interactive tutorial for aidev
"""
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from aidev.config import ConfigManager
from aidev.profiles import ProfileManager
from aidev.mcp import MCPManager

console = Console()


class Tutorial:
    """Interactive tutorial system"""

    def __init__(
        self,
        config_manager: ConfigManager,
        profile_manager: ProfileManager,
        mcp_manager: MCPManager,
    ):
        """Initialize tutorial"""
        self.config_manager = config_manager
        self.profile_manager = profile_manager
        self.mcp_manager = mcp_manager
        self.current_step = 0
        self.completed_steps = []

    def run(self) -> None:
        """Run the full tutorial"""
        console.clear()
        self._show_welcome()

        if not Confirm.ask("\nWould you like to start the interactive tutorial?", default=True):
            console.print("\n[dim]You can run this tutorial anytime with: [cyan]ai learn[/cyan][/dim]")
            return

        steps = [
            self._step_1_setup,
            self._step_2_profiles,
            self._step_3_env,
            self._step_4_mcp,
            self._step_5_project,
            self._step_6_next_steps,
        ]

        for i, step in enumerate(steps):
            self.current_step = i + 1
            try:
                step()
                self.completed_steps.append(i + 1)
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Tutorial paused. Run 'ai learn' to continue anytime.[/yellow]")
                return

        self._show_completion()

    def _show_welcome(self) -> None:
        """Show welcome message"""
        welcome = Panel.fit(
            "[bold cyan]Welcome to aidev![/bold cyan]\n\n"
            "This interactive tutorial will guide you through:\n"
            "  • Initial setup and configuration\n"
            "  • Managing profiles for different workflows\n"
            "  • Setting up environment variables\n"
            "  • Installing MCP servers\n"
            "  • Using aidev in your projects\n\n"
            "[dim]Estimated time: 5-10 minutes[/dim]",
            border_style="cyan",
        )
        console.print(welcome)

    def _step_1_setup(self) -> None:
        """Step 1: Setup"""
        console.print(f"\n[bold]Step {self.current_step}/6: Initial Setup[/bold]")
        console.print("─" * 60)

        console.print(
            "\nFirst, let's make sure aidev is initialized.\n"
            "This creates the ~/.aidev directory with all configuration files.\n"
        )

        if self.config_manager.is_initialized():
            console.print("[green]✓[/green] aidev is already initialized!")
        else:
            console.print("[yellow]aidev is not initialized yet.[/yellow]")
            if Confirm.ask("\nWould you like to initialize it now?", default=True):
                self.config_manager.init_directories()
                self.profile_manager.init_builtin_profiles()
                self.mcp_manager.init_builtin_servers()
                console.print("\n[green]✓[/green] aidev initialized successfully!")
            else:
                console.print("\n[yellow]Skipping initialization.[/yellow]")

        self._wait_for_next()

    def _step_2_profiles(self) -> None:
        """Step 2: Profiles"""
        console.print(f"\n[bold]Step {self.current_step}/6: Understanding Profiles[/bold]")
        console.print("─" * 60)

        console.print(
            "\nProfiles are pre-configured sets of MCP servers and environment\n"
            "variables for different workflows.\n\n"
            "[bold]Built-in profiles:[/bold]\n"
            "  • [cyan]web[/cyan]   - Web/app development (git, github, filesystem)\n"
            "  • [cyan]qa[/cyan]    - Testing workflows (git, duckduckgo, filesystem)\n"
            "  • [cyan]infra[/cyan] - Infrastructure (git, gitlab, k8s, docker)\n"
        )

        profiles = self.profile_manager.list_profiles()
        if profiles:
            console.print(f"\n[green]✓[/green] You have {len(profiles)} profiles available")

        console.print(
            "\n[bold]Useful commands:[/bold]\n"
            "  [cyan]ai profile list[/cyan]           - List all profiles\n"
            "  [cyan]ai profile show web[/cyan]       - View profile details\n"
            "  [cyan]ai profile clone web my-web[/cyan] - Clone and customize\n"
        )

        self._wait_for_next()

    def _step_3_env(self) -> None:
        """Step 3: Environment Variables"""
        console.print(f"\n[bold]Step {self.current_step}/6: Environment Variables[/bold]")
        console.print("─" * 60)

        console.print(
            "\nEnvironment variables store API keys and credentials.\n"
            "aidev manages them centrally in ~/.aidev/.env\n\n"
            "[bold]Common variables:[/bold]\n"
            "  • ANTHROPIC_API_KEY - For Claude AI\n"
            "  • GITHUB_TOKEN - For GitHub integration\n"
            "  • DATABASE_URL - Database connection string\n"
        )

        env = self.config_manager.get_env()
        if env:
            console.print(f"\n[green]✓[/green] You have {len(env)} environment variables set")
        else:
            console.print("\n[yellow]No environment variables set yet.[/yellow]")

        console.print(
            "\n[bold]Useful commands:[/bold]\n"
            "  [cyan]ai env set GITHUB_TOKEN ghp_xxx[/cyan] - Set variable\n"
            "  [cyan]ai env list[/cyan]                      - List all (masked)\n"
            "  [cyan]ai env validate[/cyan]                  - Validate against profile\n"
        )

        self._wait_for_next()

    def _step_4_mcp(self) -> None:
        """Step 4: MCP Servers"""
        console.print(f"\n[bold]Step {self.current_step}/6: MCP Servers[/bold]")
        console.print("─" * 60)

        console.print(
            "\nMCP servers add capabilities to your AI tools.\n"
            "Think of them as plugins that let AI interact with:\n"
            "  • Filesystems and git repositories\n"
            "  • Databases (PostgreSQL, MySQL, etc.)\n"
            "  • Cloud services (AWS, GCP, etc.)\n"
            "  • Development tools (GitHub, GitLab, etc.)\n"
        )

        installed = self.mcp_manager.list_installed()
        if installed:
            console.print(f"\n[green]✓[/green] You have {len(installed)} MCP servers installed")
        else:
            console.print("\n[yellow]No MCP servers installed yet.[/yellow]")

        console.print(
            "\n[bold]Useful commands:[/bold]\n"
            "  [cyan]ai mcp search kubernetes[/cyan]  - Search for servers\n"
            "  [cyan]ai mcp install postgres[/cyan]   - Install a server\n"
            "  [cyan]ai mcp list[/cyan]                - List installed\n"
            "  [cyan]ai mcp test postgres[/cyan]       - Test connectivity\n"
        )

        self._wait_for_next()

    def _step_5_project(self) -> None:
        """Step 5: Project Setup"""
        console.print(f"\n[bold]Step {self.current_step}/6: Using aidev in Projects[/bold]")
        console.print("─" * 60)

        console.print(
            "\nTo use aidev in a project:\n\n"
            "[bold]1. Auto-detect and setup:[/bold]\n"
            "   [cyan]cd ~/my-project[/cyan]\n"
            "   [cyan]ai quickstart[/cyan]\n"
            "   → Detects your stack and recommends a profile\n\n"
            "[bold]2. Or manually initialize:[/bold]\n"
            "   [cyan]ai init --profile web[/cyan]\n"
            "   → Creates .aidev/config.json with your profile\n\n"
            "[bold]3. Launch AI tools:[/bold]\n"
            "   [cyan]ai cursor[/cyan]           # Launch Cursor with profile\n"
            "   [cyan]ai claude --profile infra[/cyan] # Override profile\n"
        )

        console.print(
            "\n[bold]Profile switching:[/bold]\n"
            "  [cyan]ai use qa[/cyan]      - Switch to QA profile\n"
            "  [cyan]ai status[/cyan]      - Show current profile + servers\n"
        )

        self._wait_for_next()

    def _step_6_next_steps(self) -> None:
        """Step 6: Next Steps"""
        console.print(f"\n[bold]Step {self.current_step}/6: Next Steps[/bold]")
        console.print("─" * 60)

        console.print(
            "\n[bold cyan]Recommended workflow:[/bold cyan]\n\n"
            "[bold]1. Set up your environment:[/bold]\n"
            "   [cyan]ai env set ANTHROPIC_API_KEY sk-ant-xxx[/cyan]\n"
            "   [cyan]ai env set GITHUB_TOKEN ghp_xxx[/cyan]\n\n"
            "[bold]2. Navigate to a project:[/bold]\n"
            "   [cyan]cd ~/my-project[/cyan]\n"
            "   [cyan]ai quickstart[/cyan]\n\n"
            "[bold]3. Launch your tool:[/bold]\n"
            "   [cyan]ai cursor[/cyan]\n\n"
            "[bold]4. Customize as needed:[/bold]\n"
            "   [cyan]ai config[/cyan]              # TUI editor\n"
            "   [cyan]ai profile clone web custom[/cyan] # Create custom profile\n"
        )

        console.print(
            "\n[bold]Helpful resources:[/bold]\n"
            "  • [cyan]ai --help[/cyan]           - Command reference\n"
            "  • [cyan]ai doctor[/cyan]           - Health check\n"
            "  • [cyan]ai profile templates[/cyan] - Pre-built templates\n"
            "  • [cyan]ai completion bash[/cyan]  - Shell completions\n"
        )

    def _show_completion(self) -> None:
        """Show completion message"""
        console.print("\n" + "=" * 60)
        completion = Panel.fit(
            "[bold green]Tutorial Complete! 🎉[/bold green]\n\n"
            f"You completed all {len(self.completed_steps)} steps.\n\n"
            "You're now ready to use aidev!\n\n"
            "[dim]Tip: Run [cyan]ai doctor[/cyan] to check your setup anytime.[/dim]",
            border_style="green",
        )
        console.print(completion)

    def _wait_for_next(self) -> None:
        """Wait for user to continue"""
        console.print()
        Prompt.ask("[dim]Press Enter to continue...[/dim]", default="")
