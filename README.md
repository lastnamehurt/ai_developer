# Universal AI Development Environment Manager

A universal, profile-based configuration manager for AI development tools that makes onboarding to new machines, projects, and contexts fast and consistent. Use `ai quickstart` to auto-detect your project stack and pick a profile, or set one explicitly.

## Why aidev?

Managing AI development tools (Cursor, Claude Code, Zed) across different projects and machines is painful:
- 🔐 API keys and credentials scattered everywhere
- 🔧 Different MCP server configurations per project
- 💻 Tedious setup on new machines
- 🔄 No easy way to share configurations

**aidev solves this** with:
- ✅ Profile-based MCP configurations (web, qa, infra)
- ✅ Centralized environment variable management
- ✅ One-command tool launching with full context
- ✅ Easy backup/restore for new machine setup
- ✅ MCP server registry for discovering new capabilities

## Quick Start

### Installation

```bash
# Install without cloning (recommended)
curl -fsSL https://raw.githubusercontent.com/lastnamehurt/aidev/main/install.sh | bash

# Or install from a local clone
git clone https://github.com/lastnamehurt/aidev.git
cd aidev

# Run installation script
./install.sh
```

### First Use

```bash
# 1. Set up aidev (interactive wizard)
ai setup

# 2. Configure your API keys
ai env set GITHUB_TOKEN ghp_your_token_here
ai env set ANTHROPIC_API_KEY sk-ant-your-key-here

# 3. Navigate to a project and initialize (auto-detect stack)
cd ~/my-project
ai quickstart        # detects JS/Python/Docker/K8s signals and recommends a profile
# or force a profile:
# ai quickstart --profile infra --yes

# 4. Launch your AI tool with a profile
ai cursor                      # Default/recommended profile
ai cursor --profile infra      # Infra profile (K8s, Docker, Git)
ai claude --profile qa         # QA profile
```

## Core Features

### 1. Profile-Based Configuration

Profiles are pre-configured sets of MCP servers and environment variables for different workflows:

```bash
ai profile list                # List all profiles
ai profile show infra          # Show profile details
ai profile create my-profile   # Create custom profile
ai use web                     # Switch active profile for this project
ai status                      # Show active profile, MCP servers, env requirements
```

**Built-in Profiles:**

| Profile | Use Case | MCP Servers |
|---------|----------|-------------|
| `web` | Web/app development | filesystem, git, github, memory-bank |
| `qa` | Quality/testing | filesystem, git, duckduckgo, memory-bank |
| `infra` | Infrastructure/deployment | filesystem, git, gitlab, k8s, atlassian |
| `default` | Alias of `web` | extends `web` |

### 2. Environment Management

Single source of truth for API keys and credentials:

```bash
ai env set GITHUB_TOKEN ghp_xxx     # Set global variable
ai env set ANTHROPIC_API_KEY sk-ant-xxx
ai env list                          # List all (masks secrets)
ai env get GITHUB_TOKEN              # Get specific variable
```

### 3. MCP Server Registry

Discover and install community MCP servers:

```bash
ai mcp search kubernetes        # Search registry
ai mcp install kubernetes       # Install server
ai mcp list                     # List installed
ai mcp test kubernetes          # Test connectivity
ai mcp remove kubernetes        # Remove server
```

### 4. Tool Launcher

Launch AI tools with automatic configuration injection:

```bash
ai cursor                       # Launch Cursor
ai cursor --profile infra      # Launch with infra profile
ai claude                       # Launch Claude Code
ai zed                          # Launch Zed
ai gemini                       # Launch Gemini Code Assist
ai codex                        # Launch Codex CLI
ai tool <name>                  # Launch any registered tool
ai status                       # Show active profile, MCP servers, env requirements
ai use <profile>                # Switch project profile
```

### 5. Backup & Restore

Easy machine migration and configuration sharing:

```bash
ai backup                       # Create backup (aidev-hostname-timestamp.tar.gz)
ai backup --output backup.tar.gz

ai restore backup.tar.gz        # Restore on new machine

aidev export config.json           # Export without secrets (for sharing)
aidev import config.json           # Import shared config
```

## Directory Structure

```
~/.aidev/                          # Main configuration directory
├── config/
│   ├── profiles/                  # Built-in profiles
│   │   ├── default.json
│   │   ├── web.json
│   │   ├── qa.json
│   │   ├── infra.json
│   │   └── custom/                # Your custom profiles
│   ├── mcp-servers/               # MCP server configurations
│   │   ├── filesystem.json
│   │   └── custom/
│   └── tools.json                 # Detected AI tools
├── .env                           # Global environment variables
├── memory-banks/                  # Persistent AI memory
├── plugins/                       # Custom plugins
├── cache/                         # Cached data
└── logs/                          # Operation logs

# Per-project
.aidev/
├── config.json                    # Project-specific settings
├── .env                           # Project environment variables
└── profile                        # Active profile name
```

## CLI Reference

### Setup & Management
```bash
aidev setup                        # Interactive setup wizard
aidev doctor                       # Health check
aidev --version                    # Show version
```

### Project Commands
```bash
aidev init [--profile NAME]        # Initialize project
aidev config set KEY VALUE         # Set project config
aidev config get KEY               # Get project config
aidev config list                  # List all config
```

### Environment Variables
```bash
aidev env set KEY VALUE            # Set variable
aidev env get KEY                  # Get variable
aidev env list                     # List all (masks secrets)
```

### Profile Management
```bash
aidev profile list                 # List profiles
aidev profile show NAME            # Show details
aidev profile create NAME          # Create custom profile
aidev profile edit NAME            # Edit profile
aidev profile export NAME          # Export for sharing
aidev profile import FILE          # Import profile
```

### MCP Servers
```bash
aidev mcp list                     # List installed servers
aidev mcp search QUERY             # Search registry
aidev mcp install NAME             # Install server
aidev mcp remove NAME              # Remove server
aidev mcp test NAME                # Test connectivity
```

### Tool Launching
```bash
aidev cursor [--profile NAME]      # Launch Cursor
aidev claude [--profile NAME]      # Launch Claude Code
aidev zed [--profile NAME]         # Launch Zed
aidev tool NAME [--profile NAME]   # Launch any tool
```

### Backup & Migration
```bash
aidev backup [--output FILE]       # Create backup
aidev restore FILE                 # Restore backup
```

## Creating Custom Profiles

Create a profile for your specific workflow:

```bash
# Create new profile
aidev profile create my-workflow --extends default

# Edit the profile JSON
aidev profile edit my-workflow
```

Example custom profile (`~/.aidev/config/profiles/custom/my-workflow.json`):

```json
{
  "name": "my-workflow",
  "description": "My custom development workflow",
  "extends": "default",
  "mcp_servers": [
    {
      "name": "github",
      "enabled": true,
      "config": {
        "owner": "myorg"
      }
    },
    {
      "name": "postgres",
      "enabled": true
    }
  ],
  "environment": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "DATABASE_URL": "${DATABASE_URL}"
  },
  "tools": {
    "cursor": {
      "enabled": true
    }
  }
}
```

## Migration Guide

### New Machine Setup

On old machine:
```bash
aidev backup --output aidev-backup.tar.gz
# Copy aidev-backup.tar.gz to new machine
```

On new machine:
```bash
# Install aidev
git clone https://github.com/lastnamehurt/aidev.git
cd aidev && ./install.sh

# Restore configuration
aidev restore aidev-backup.tar.gz

# Verify
aidev doctor
```

### Sharing Configurations

Share profiles with your team (without secrets):

```bash
# Export
aidev profile export my-workflow --output my-workflow.json

# Share my-workflow.json with team

# Team member imports
aidev profile import my-workflow.json
```

## Development

### Project Structure

```
aidev/
├── src/aidev/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── config.py           # Configuration management
│   ├── profiles.py         # Profile system
│   ├── mcp.py              # MCP server registry
│   ├── tools.py            # Tool detection/launching
│   ├── backup.py           # Backup/restore
│   ├── models.py           # Pydantic data models
│   ├── constants.py        # Constants and defaults
│   └── utils.py            # Utility functions
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docs/                   # Documentation
├── examples/               # Example configurations
├── pyproject.toml          # Project metadata
└── install.sh              # Installation script
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=aidev --cov-report=html

# Run specific tests
pytest tests/unit/test_profiles.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff src/ tests/

# Type check
mypy src/
```

## Troubleshooting

### Command not found: aidev

```bash
# Add to PATH
echo 'export PATH="$HOME/.local/aidev/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or use full path
~/.local/aidev/bin/aidev --version
```

### Environment variables not loading

```bash
# Check setup
aidev doctor

# List variables
aidev env list

# Test loading
aidev env get GITHUB_TOKEN
```

### AI tool not launching

```bash
# Check if tool is installed
which cursor
which claude

# Check aidev configuration
aidev doctor

# Test tool directly
cursor --version
```

## Roadmap

- [ ] PyPI package distribution
- [ ] Homebrew formula
- [ ] Windows support (native, not just WSL)
- [ ] Web UI for configuration
- [ ] Team/organization profiles
- [ ] Cloud backup/sync
- [ ] Plugin marketplace
- [ ] MCP server development templates

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Inspired by the original company-built version, rebuilt as a universal personal project.

Built with:
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
