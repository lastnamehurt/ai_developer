# aidev - Universal AI Development Environment Manager

**One command to configure all your AI development tools across any project or machine.**

## ❓What is aidev?

`aidev` is a unified command-line interface that simplifies managing AI development tools (Claude Code, Cursor, Codex, Gemini) across projects and machines. Stop juggling API keys, MCP server configs, and tool-specific settings—`aidev` centralizes everything.

## ✨ Key Features

- **🎭 Profile System** - Switch between AI roles instantly (web dev, infrastructure, QA, etc.)
- **🔄 Workflow Orchestration** - Multi-step AI tasks across different assistants with retries and resumable execution
- **🔌 MCP Server Management** - Discover, install, and manage Model Context Protocol servers
- **🔐 Environment Management** - Centralized, encrypted storage for API keys and secrets
- **🚀 Smart Quickstart** - Auto-detect project stack and configure optimal profiles
- **🛠️ Tool Launcher** - Launch Claude, Cursor, Codex, Gemini, Ollama with automatic config injection
- **🤖 Local AI Development** - Aider + Ollama integration for cost-effective, private coding
- **📊 Interactive TUI** - Visual configuration management
- **🔍 Health Checks** - Diagnose setup issues with actionable fixes
- **📝 Code Review** - Lightweight code review directly from CLI

👉 **[See all features →](docs/features.md)**

## 🚀 Quick Start

### Installation

```bash
# Recommended: Install with pipx (isolated, no venv activation needed)
pipx install "git+https://github.com/lastnamehurt/ai_developer.git@main"

# Verify installation
ai --version
```

### First Run

```bash
# 1. Initialize aidev
ai setup

# 2. Add your API keys (encrypted storage)
ai env set ANTHROPIC_API_KEY sk-ant-xxx
ai env set GITHUB_TOKEN ghp_xxx

# 3. Navigate to your project and auto-configure
cd ~/my-project
ai quickstart

# 4. Launch your AI tool
ai claude    # or ai cursor, ai codex, ai gemini
```

## 📚 Documentation

### Core Systems

- **[Features Overview](docs/features.md)** - Complete feature guide
- **[Profile System](docs/profiles.md)** - Switch AI roles and contexts
- **[Workflow Orchestration](docs/workflows.md)** - Multi-step AI task automation
- **[MCP Server Management](docs/mcp_browser.md)** - Extend capabilities with MCP servers
- **[Memory Bank](docs/memory_server_docs.md)** - Persistent project memory

### Guides & References

- **[Commands Reference](docs/commands.md)** - Complete command cheat sheet
- **[Architecture](docs/architecture.md)** - System design and internals
- **[DX Engineer Workflows](docs/dx-engineer-workflows.md)** - Specialized workflows for developer experience
- **[Aider & Ollama Integration](docs/aider-ollama-integration.md)** - Local-first AI development with Aider and Ollama

## 💡 Common Workflows

### Profile Management

```bash
ai profile list              # List all profiles
ai use web                   # Switch to web development profile
ai use infra                 # Switch to infrastructure profile
ai status                    # Show current profile and config
```

👉 **[Profile Guide →](docs/profiles.md)**

### Workflow Execution

```bash
ai workflow list                              # Show available workflows
ai workflow sync_branch                       # Rebase branch onto main
ai workflow doc_improver README.md            # Improve documentation
ai workflow onboarding_guide                  # Create onboarding guide
ai workflow status                            # Check workflow status
```

👉 **[Workflow Guide →](docs/workflows.md)**

### MCP Server Management

```bash
ai mcp browse                # Visual browser (TUI)
ai mcp search kubernetes     # Search registry
ai mcp install gitlab        # Install server
ai mcp test gitlab           # Test connectivity
```

👉 **[MCP Browser Guide →](docs/mcp_browser.md)**

### Environment Variables

```bash
ai env set KEY value [--project] [--encrypt]  # Set variable
ai env list                                   # List all variables
ai env validate                               # Check for missing vars
```

### Local AI Development (Aider + Ollama)

```bash
# Use Aider for terminal-first pair programming
ai use aider
aider --model claude-sonnet-4-5

# Use Ollama for local, private code review
ai review --staged --provider ollama

# Combine: Local development with Ollama, complex tasks with Claude
aider --model ollama/codellama  # Free, private
aider --model claude-sonnet-4-5  # Powerful, cloud-based
```

👉 **[Aider & Ollama Integration Guide →](docs/aider-ollama-integration.md)**

## 🛠️ Troubleshooting

```bash
ai doctor                    # Run health checks and get fixes
```

Common issues:
- **Command not found**: Ensure pipx/pip bin directory is on `PATH` (`pipx ensurepath`)
- **Missing secrets**: Add with `ai env set KEY value` and unlock with `ai env unlock`
- **MCP connectivity**: Test with `ai mcp test <server-name>`
- **Upgrade**: `pipx upgrade aidev`

## 🏗️ Architecture

Configuration is stored in:

```
~/.aidev/                    # Global config
├── config/profiles/         # Profile definitions
├── .env                     # Encrypted environment variables
└── cache/                   # MCP registry cache

./.aidev/                    # Project-specific config
├── config.json             # Project settings
├── .env                     # Project env vars
└── profile                  # Active profile
```

👉 **[Architecture Details →](docs/architecture.md)**

## 🧑‍💻 Development

```bash
# Clone and setup
git clone https://github.com/lastnamehurt/ai_developer.git
cd ai_developer
pip install -e ".[dev]"

# Run tests
pytest

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/
```

👉 **[Development Guide →](CLAUDE.md)**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development guidelines.

---

**Built with:** [Click](https://click.palletsprojects.com/) • [Rich](https://rich.readthedocs.io/) • [Textual](https://textual.textualize.io/) • [Pydantic](https://docs.pydantic.dev/)
