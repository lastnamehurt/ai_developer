# aidev - Universal AI Development Environment Manager

**One command to configure all your AI development tools across any project or machine.**

Stop managing scattered API keys, MCP server configs, and tool setups manually. Use profiles to instantly switch contexts and launch AI tools with full configuration.

## The Problem

Managing AI development tools (Claude Code, Cursor, Codex, Gemini) is painful:
- 🔐 API keys scattered across multiple `.env` files
- 🔧 MCP server configs manually edited per tool
- 💻 30+ minutes setting up each new machine
- 🔄 No way to share configurations with your team

## The Solution

```bash
# Auto-detect your project and configure everything
ai quickstart

# Switch profiles instantly
ai use web          # Web development
ai use infra        # Kubernetes + Docker
ai use qa           # Testing workflows

# Launch tools with full context
ai claude           # Launch with active profile + MCP servers + env vars
ai claude --profile infra
ai cursor --profile web
```

## Quick Start

### Installation

```bash
# Install (creates ~/.local/aidev and adds to PATH)
curl -fsSL https://raw.githubusercontent.com/lastnamehurt/ai_developer/main/install.sh | bash

# Or from source
git clone https://github.com/lastnamehurt/ai_developer.git
cd ai_developer && ./install.sh
```

### First Run

```bash
# 1. Initial setup
ai setup

# 2. Add your API keys (stored in ~/.aidev/.env)
ai env set ANTHROPIC_API_KEY sk-ant-xxx
ai env set GITHUB_TOKEN ghp_xxx

# 3. Navigate to a project and auto-configure
cd ~/my-nextjs-app
ai quickstart
# 🔍 Analyzing project...
# ✓ Detected: Next.js + PostgreSQL
# 💡 Recommended profile: web
# ✓ Configured MCP servers: filesystem, git, github, memory-bank

# 4. Launch your tool
ai claude
```

## Core Features

### 1. Smart Quickstart

Auto-detect your stack and configure the right profile:

```bash
ai quickstart
# Detects: package.json, tsconfig.json, docker-compose.yml
# Recommends: web profile
# Configures: filesystem, git, github, postgres MCP servers
```

**Supported detection:**
- JavaScript/TypeScript (Next.js, React, Node)
- Python (Django, FastAPI, Flask)
- Docker & Kubernetes
- Databases (PostgreSQL, MySQL, Redis)

### 2. Profile System

Pre-configured profiles for different workflows:

| Profile | Use Case | MCP Servers |
|---------|----------|-------------|
| `web` | Web/API development | filesystem, git, github, memory-bank |
| `qa` | Testing & quality assurance | filesystem, git, duckduckgo, memory-bank |
| `infra` | Infrastructure & K8s | filesystem, git, gitlab, k8s, atlassian |
| `default` | General development | Alias of `web` |

**Profile commands:**
```bash
ai profile list                 # Show all profiles
ai profile show web             # View profile details
ai profile clone web my-web     # Clone and customize
ai profile diff web infra       # Compare profiles
ai use infra                    # Switch active profile
ai status                       # Show current profile + servers
```

### 3. Environment Management

Centralized secrets with global + project scope:

```bash
# Global (all projects)
ai env set GITHUB_TOKEN ghp_xxx

# Project-specific (overrides global)
ai env set DATABASE_URL postgres://localhost --project

# List (auto-masks secrets)
ai env list
# Global:
#   GITHUB_TOKEN: ghp-***xxx
# Project:
#   DATABASE_URL: postgres://***

# Validate against profile requirements
ai env validate
# ✓ All required keys present
# ⚠ OPENAI_API_KEY set but not used
```

### 4. MCP Server Management

Discover, install, and manage MCP servers:

```bash
# Search the registry
ai mcp search kubernetes
# ⭐ kubernetes - Manage K8s clusters and deployments

# Browse registry in a TUI
ai mcp browse
# Filter by tags, view details, and install directly

# Install and auto-configure
ai mcp install kubernetes
# ✓ Installed kubernetes
# 💡 Works great with 'infra' profile
# Add to current profile? [Y/n]

# Test connectivity
ai mcp test kubernetes
# ✓ kubernetes: Connected
# ✓ Found 3 clusters

# List installed
ai mcp list
# Installed MCP Servers:
#   ✓ filesystem (built-in)
#   ✓ git (built-in)
#   ✓ kubernetes
```

### 5. Tool Launcher

Launch AI tools with automatic config injection:

```bash
ai cursor                       # Use active profile
ai cursor --profile infra       # Override profile
ai claude                       # Launch Claude Code
ai codex                        # Launch Codex CLI
ai gemini                       # Launch Gemini Code Assist
```

**What happens behind the scenes:**
1. Loads profile (e.g., `web`)
2. Merges global + project env vars
3. Generates tool-specific MCP config (`~/.cursor/mcp.json`, `~/.claude/mcp.json`)
4. Validates required env vars are set
5. Launches tool with full context

### 6. Interactive TUI

Visual configuration editor:

```bash
ai config
# Launches Textual TUI to:
# - Browse and toggle MCP servers
# - Edit environment variables
# - Switch profiles visually
# - See live preview
```

### 7. Health Checks

Preflight validation with actionable fixes:

```bash
ai doctor
# ✓ aidev initialized
# ✓ git binary found
# ✗ ANTHROPIC_API_KEY not set
#
# Fix: ai env set ANTHROPIC_API_KEY sk-ant-xxx
# Get key: https://console.anthropic.com/
```

## Advanced Usage

### Custom Profiles

```bash
# Clone and customize
ai profile clone web my-fullstack
ai profile clone web my-fullstack -m "git,github,postgres,redis"

# Create from scratch
ai profile create mobile --extends web
# Edit: ~/.aidev/config/profiles/custom/mobile.json

# Share with team
ai profile export mobile --output mobile.json
# Team imports:
ai profile import mobile.json
```

### Project Workflow

```bash
# Initialize new project
cd ~/new-project
ai init --profile web

# Switch profiles per project
ai use qa        # For testing
ai use infra     # For deployment work

# Check current config
ai status
# Profile: qa
# MCP Servers: ✓ filesystem ✓ git ✓ duckduckgo ✓ memory-bank
# Environment: ✓ ANTHROPIC_API_KEY
```

### Machine Migration

```bash
# On old machine
ai backup --output aidev-backup.tar.gz

# On new machine
curl -fsSL https://install.aidev.sh | bash
ai restore aidev-backup.tar.gz
ai doctor  # Verify
```

## Architecture

```
~/.aidev/
├── config/
│   ├── profiles/          # Built-in profiles
│   │   ├── web.json
│   │   ├── qa.json
│   │   └── infra.json
│   └── profiles/custom/   # Your custom profiles
├── .env                   # Global environment variables
└── cache/                 # MCP registry cache

.aidev/                    # Per-project
├── config.json            # Project settings
├── .env                   # Project-specific env vars
└── profile                # Active profile name
```

**How it works:**
- Profiles define MCP servers + env requirements
- `ai quickstart` detects stack and recommends profile
- `ai cursor` generates tool config from active profile
- Global env + project env merge (project wins)
- See `docs/architecture.md` for flow diagrams

## Development

### Setup

```bash
git clone https://github.com/lastnamehurt/ai_developer.git
cd ai_developer
pip install -e ".[dev]"
```

### Testing

```bash
pytest                              # All tests
pytest tests/unit                   # Unit tests only
pytest --cov=aidev --cov-report=html  # With coverage
```

### Code Quality

```bash
black src/ tests/      # Format
ruff src/ tests/       # Lint
mypy src/              # Type check
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make changes and add tests
4. Run quality checks (`black`, `ruff`, `mypy`, `pytest`)
5. Commit with descriptive messages
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [Click](https://click.palletsprojects.com/) + [Rich-Click](https://github.com/ewels/rich-click) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Textual](https://textual.textualize.io/) - TUI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**Questions?** Open an issue at [github.com/lastnamehurt/ai_developer/issues](https://github.com/lastnamehurt/ai_developer/issues)
