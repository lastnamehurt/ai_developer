# aidev - Universal AI Development Environment Manager

**One command to configure all your AI development tools across any project or machine.**

## Introduction

Managing AI development tools (like Claude Code, Cursor, Codex, or Gemini) can be fragmented and time-consuming. From scattered API keys and manual configuration of MCP servers to lengthy setup times for new machines and lack of team-wide sharing, these challenges hinder productivity.

`aidev` simplifies this by providing a unified command-line interface to manage all your AI development environments. Use profiles to instantly switch contexts, centralize your secrets, and launch AI tools with full, consistent configurations.

## ✨ Features

*   **Smart Quickstart**: Automatically detects your project's tech stack and configures an optimal profile and MCP servers.
*   **Profile System**: Define and switch between pre-configured or custom profiles tailored for different workflows (e.g., web dev, infrastructure, QA).
*   **Environment Management**: Centralized, encrypted storage for API keys and other environment variables, with global and project-specific scopes.
*   **MCP Server Management**: Discover, install, and manage custom AI backend (MCP) servers to extend `aidev`'s capabilities.
*   **Tool Launcher**: Seamlessly launch integrated AI tools (Claude, Cursor, Codex, Gemini) with all relevant configurations injected automatically.
*   **Interactive TUI**: A terminal user interface for visual configuration editing and management of profiles, environments, and MCP servers.
*   **Health Checks**: Diagnose common setup issues with `ai doctor`, providing actionable fixes to keep your environment running smoothly.
*   **Lightweight Code Review**: Perform quick, heuristic-based code reviews on staged, all tracked, or specified files directly from the CLI.

## 🚀 Quick Start

Get `aidev` up and running in minutes.

### Installation

The recommended way to install `aidev` is using `pipx` for isolated, system-wide access without virtual environment activation.

```bash
# Recommended: Install with pipx (isolated, no venv activation needed)
pipx install "git+https://github.com/lastnamehurt/ai_developer.git@main"

# If you've cloned the repository and want to install from source:
# git clone https://github.com/lastnamehurt/ai_developer.git
# cd ai_developer && pipx install .

# Fallback: Install with pip (system or user scope)
# pip install "git+https://github.com/lastnamehurt/ai_developer.git@main"
```

### First Run

Follow these steps to set up `aidev` and configure your first project:

1.  **Initialize `aidev`**:
    ```bash
    ai setup
    ```

2.  **Add your API keys**: Store sensitive credentials securely. `aidev` encrypts these in `~/.aidev/.env`.
    ```bash
    ai env set ANTHROPIC_API_KEY sk-ant-xxx
    ai env set GITHUB_TOKEN ghp_xxx
    # For encrypted storage:
    ai env set --encrypt OPENAI_API_KEY sk-openai-xxx
    ```

3.  **Navigate to your project and auto-configure**:
    ```bash
    cd ~/my-nextjs-app
    ai quickstart
    # Output will show detected stack and recommended profile, e.g.:
    # 🔍 Analyzing project...
    # ✓ Detected: Next.js + PostgreSQL
    # 💡 Recommended profile: web
    # ✓ Configured MCP servers: filesystem, git, github, memory-bank
    ```

4.  **Launch your AI tool**: `aidev` will automatically inject the correct context.
    ```bash
    ai claude            # Launch Claude Code with your active profile
    ai cursor --profile infra # Launch Cursor with a specific profile
    ```

## 📖 In-Depth Guides

Explore `aidev`'s capabilities in more detail:

### Profile Management

`aidev` uses profiles to define collections of environment variables and MCP server configurations, allowing you to quickly switch between different development contexts.

```bash
ai profile list                 # Show all available profiles
ai profile show web             # View details of a specific profile
ai profile clone web my-web     # Create a custom profile based on an existing one
ai profile diff web infra       # Compare two profiles
ai use infra                    # Switch your active profile to 'infra'
ai status                       # Display your current active profile and configured servers
```

### Environment Variables

Manage all your secrets and configurations centrally.

```bash
# Global environment variable (available across all projects)
ai env set GITHUB_TOKEN ghp_xxx

# Project-specific environment variable (overrides global if same name)
ai env set DATABASE_URL postgres://localhost --project

ai env list                     # List configured environment variables (secrets are masked)
ai env validate                 # Check for missing required variables for your active profile
ai env unlock                   # Unlock encrypted variables for use
```

### MCP Server Management

MCP (Multi-Capability Platform) servers are `aidev`'s way of extending its reach to various tools and services.

```bash
ai mcp search kubernetes        # Find MCP servers in the registry
ai mcp browse                   # Launch a TUI to visually browse and install MCP servers
ai mcp install kubernetes       # Install a new MCP server
ai mcp test kubernetes          # Verify connectivity to an installed MCP server
ai mcp list                     # List all installed MCP servers
```

### Tool Integration

`aidev` acts as a launcher, preparing the environment and configuration for your preferred AI development tools.

```bash
ai cursor                       # Launch Cursor using your active profile's configuration
ai claude                       # Launch Claude Code
ai codex                        # Launch Codex CLI
ai gemini                       # Launch Gemini Code Assist
```

### Interactive Configuration (TUI)

For a visual way to manage your `aidev` setup, use the interactive TUI.

```bash
ai config
# Launches a Textual TUI to:
# - Browse and toggle MCP servers
# - Edit environment variables
# - Switch profiles visually
# - See live configuration previews
```

### System Health Checks

Ensure `aidev` and its dependencies are correctly configured.

```bash
ai doctor
# Runs a series of checks and provides actionable advice for any issues found.
```

### Lightweight Code Review

Get instant feedback on your code using `aidev`'s built-in heuristic-based reviewer or external tools.

```bash
ai review --staged              # Review changes in your Git staging area
ai review --all                 # Review all tracked files in your repository
ai review app.py util.py        # Review specific files
```
You can also configure external reviewers (e.g., Aider, Ollama) in `~/.aidev/review.json`.

## 🏗️ Advanced Usage

### Custom Profiles

Extend `aidev` to fit your unique needs.

```bash
ai profile clone web my-fullstack           # Clone an existing profile to customize
ai profile create mobile --extends web      # Create a new profile inheriting from 'web'
# Edit your custom profile files in ~/.aidev/config/profiles/custom/

ai profile export my-profile --output my-profile.json # Share your custom profile
ai profile import shared-profile.json       # Import profiles from your team
```

### Project Workflow

Initialize and manage `aidev` configurations on a per-project basis.

```bash
cd ~/new-project
ai init --profile web                       # Initialize a new project with a specific profile

# Switch profiles based on current task
ai use qa                                   # For testing workflows
ai use infra                                # For deployment work

ai status                                   # Quickly see the active profile and environment for the current project
```

### Machine Migration

Easily migrate your `aidev` configuration between machines.

```bash
# On your old machine:
ai backup --output aidev-config-backup.tar.gz

# On your new machine (after aidev installation):
ai restore aidev-config-backup.tar.gz
ai doctor # Verify everything is working
```

## 🏛️ Architecture

`aidev` stores its core configuration and user data in a structured directory:

```
~/.aidev/
├── config/
│   ├── profiles/          # Built-in profile definitions
│   └── profiles/custom/   # Your custom profile definitions
├── .env                   # Global environment variables (encrypted)
└── cache/                 # Cache for MCP registry data

# Per-project configuration is stored in a .aidev/ directory within your project:
./.aidev/
├── config.json            # Project-specific settings
├── .env                   # Project-specific environment variables (encrypted)
└── profile                # Active profile name for this project
```
For a detailed understanding of `aidev`'s internal workings, including flow diagrams, please refer to the `docs/architecture.md` file.

## 🧑‍💻 Development

### Setup

To contribute to `aidev`, clone the repository and set up your development environment:

```bash
git clone https://github.com/lastnamehurt/ai_developer.git
cd ai_developer
pip install -e ".[dev]"
# For encrypted environment variable support (if issues arise):
# pip install cryptography
```

### Testing

Run tests to ensure code integrity:

```bash
pytest                              # Run all tests
pytest tests/unit                   # Run only unit tests
pytest --cov=aidev --cov-report=html  # Run tests with code coverage analysis
```

### Code Quality

Maintain high code quality standards:

```bash
black src/ tests/      # Format code automatically
ruff src/ tests/       # Lint code for common issues
mypy src/              # Perform static type checking
```

### Contributing

We welcome contributions! Please see our `CONTRIBUTING.md` for guidelines.

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/my-new-feature`).
3.  Make your changes and add relevant tests.
4.  Ensure all quality checks pass (`black`, `ruff`, `mypy`, `pytest`).
5.  Commit your changes with descriptive messages.
6.  Submit a pull request.

## 🤝 Community & Support

Have questions, ideas, or need assistance?
Open an issue on our GitHub repository: [github.com/lastnamehurt/ai_developer/issues](https://github.com/lastnamehurt/ai_developer/issues)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for full details.

## 💖 Credits

`aidev` is built upon the excellent work of these open-source projects:

*   [Click](https://click.palletsprojects.com/) + [Rich-Click](https://github.com/ewels/rich-click) - Powerful CLI framework
*   [Rich](https://rich.readthedocs.io/) - Stunning terminal formatting and display
*   [Textual](https://textual.textualize.io/) - Modern TUI application framework
*   [Pydantic](https://docs.pydantic.dev/) - Robust data validation and settings management

---