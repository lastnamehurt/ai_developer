# aidev - Universal AI Development Environment Manager

**One command to configure all your AI development tools across any project or machine.**

> **Status: Active Alpha** - This project is in active development. Core features are stable and production-ready, with new capabilities being added regularly.

## 🎯 Who is this for?

**For engineers juggling multiple AI development tools** (Claude Code, Cursor, Codex, Gemini, Ollama) across different projects and machines.

### The Pain Points aidev Removes

- **Scattered Configurations**: No more manually editing JSON/TOML configs for each tool in each project
- **Manual MCP Setup**: Stop copy-pasting MCP server configs and environment variables
- **Context Switching Overhead**: Switch between web dev, infrastructure, and QA contexts instantly
- **Secret Management Chaos**: Centralized, encrypted storage for API keys and tokens
- **Onboarding Friction**: New projects require zero setup—just run `ai quickstart`

### What You Get

- **🎭 Profile System** - Switch AI roles instantly (web dev → infrastructure → QA)
- **🔄 Workflow Orchestration** - Multi-step AI tasks across different assistants
- **🔌 MCP Server Management** - Discover, install, and manage Model Context Protocol servers
- **🔐 Encrypted Secrets** - Centralized environment variable management
- **🚀 Smart Quickstart** - Auto-detect project stack and configure optimal profiles
- **🛠️ Tool Launcher** - Launch any AI tool with automatic config injection

## ❓What is aidev?

`aidev` is a unified command-line interface that simplifies managing AI development tools (Claude Code, Cursor, Codex, Gemini, Ollama) across projects and machines. Stop juggling API keys, MCP server configs, and tool-specific settings—`aidev` centralizes everything.

**Entry Points**: Both `ai` and `aidev` commands are available (aliases).

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

# Reinstall from local source (pick up latest changes)
pipx install --force /path/to/ai_developer

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

## ⭐ Hero Workflows

These workflows showcase the power of `aidev`—try them to see immediate value:

### 1. DX Engineer Debugging Pipelines

**Problem**: CI/CD pipeline failures need investigation with full repo context.

```bash
# Switch to infrastructure profile (includes GitLab, K8s MCP servers)
ai use infra

# Launch Claude with full repo context via MCP servers
ai claude

# In Claude: "Analyze why the deployment pipeline failed in PR #42"
# Claude automatically has access to GitLab issues, K8s clusters, and repo files
```

**What happens**: Claude uses GitLab MCP to fetch PR details, K8s MCP to check deployment status, and filesystem MCP to analyze code changes—all automatically configured.

### 2. Documentation Improvement Workflow

**Problem**: Need to improve documentation quality with structured analysis.

```bash
# Run the doc_improver workflow on any markdown file
ai workflow doc_improver README.md

# Or improve multiple files
ai workflow doc_improver docs/architecture.md
```

**What happens**: The workflow analyzes the doc, creates an improvement plan, and generates a ticket-ready summary—all orchestrated across multiple AI assistants.

### 3. Pre-MR Branch Critique

**Problem**: Catch security issues, bugs, and test gaps before code review.

```bash
# Run the branch_critic workflow on your current branch
ai workflow branch_critic

# Produces CRITIQUE.md and CRITIQUE_IMPLEMENTATION_TRACKER.md, then implements approved fixes
```

**What happens**: The workflow reads every changed file, fetches all linked Jira tickets via the Atlassian MCP, critiques across 7 lenses (security, correctness, tests, consistency, docs, opportunities, scope), surfaces decisions for human review, writes structured docs, then implements all approved fixes.

### 4. Onboarding New Team Members

**Problem**: New developers need to understand project architecture quickly.

```bash
# 1. Switch to web profile (includes GitHub, memory-bank MCP servers)
ai use web

# 2. Launch Claude with full project context
ai claude

# 3. Ask architecture questions:
# "Explain the authentication flow in this codebase"
# "What are the main components and how do they interact?"
# "Show me the database schema and relationships"
```

**What happens**: Claude uses GitHub MCP to read issues/PRs, memory-bank MCP to access project knowledge, and filesystem MCP to navigate code—providing comprehensive answers with full context.

## 📚 Documentation

### Getting Started

- **[System Overview](docs/system_overview.md)** - 🎯 **Start here!** Visual guide to how aidev works
- **[Features Overview](docs/features.md)** - Complete feature guide
- **[Commands Reference](docs/commands.md)** - Complete command cheat sheet

### Core Systems

- **[Profile System](docs/profiles.md)** - Switch AI roles and contexts
- **[Workflow Orchestration](docs/workflows.md)** - Multi-step AI task automation
- **[MCP Server Management](docs/mcp_browser.md)** - Extend capabilities with MCP servers
- **[Memory Bank](docs/memory_server_docs.md)** - Persistent project memory

### Guides & References

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
ai workflow                                   # Show available workflows
ai workflow branch_critic                     # Critique branch before opening MR
ai workflow doc_improver README.md            # Improve documentation
ai workflow onboarding_guide                  # Create onboarding guide
ai workflow bug_triage TICKET-123             # Triage a bug ticket
```

👉 **[Workflow Guide →](docs/workflows.md)**

### Example Workflow Definition

Workflows are defined in `.aidev/workflows.yaml`. Here's a simple 2-step workflow that switches assistants:

```yaml
workflows:
  doc_improver:
    description: "Improve documentation quality"
    tool: claude                    # Default assistant for all steps
    steps:
      - name: analyze_doc
        prompt: doc_analyzer         # References src/aidev/prompts/doc_analyzer.txt
        timeout_sec: 60
        retries: 1

      - name: draft_improvements
        prompt: doc_outline_planner
        tool: gemini                 # Override: use Gemini for this step
```

**Key Features**:
- **Assistant Switching**: Use Claude for analysis, Gemini for drafting
- **Automatic Issue Detection**: Detects Jira/GitHub/GitLab issues from input
- **File Handling**: Automatically accepts files when provided
- **Profile-Agnostic**: Uses active profile at runtime

👉 **[Full Workflow Documentation →](docs/workflows.md)**

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
# Launch Aider with aidev (recommended)
ai aider                                    # Default aider profile
ai aider --model claude-sonnet-4-5         # Use Claude
ai aider --model ollama/codellama          # Use local Ollama (free!)
ai aider --yes                              # Auto-accept changes

# Use Ollama for local, private code review
ai review --staged --provider ollama

# Workflows that use Aider
ai workflow implement_with_aider "Add user authentication"
ai workflow quick_refactor "Refactor UserService"
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
- **Upgrade from remote**: `pipx upgrade aidev`
- **Reinstall from local source**: `pipx install --force /path/to/ai_developer`

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

### Setup

```bash
# Clone and setup
git clone https://github.com/lastnamehurt/ai_developer.git
cd ai_developer
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=aidev --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_profiles.py

# Run specific test function
pytest tests/unit/test_profiles.py::TestProfileManager::test_create_profile
```

### Code Quality

```bash
# Format code (required before commits)
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

👉 **[Development Guide →](CLAUDE.md)**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development guidelines.

---

**Built with:** [Click](https://click.palletsprojects.com/) • [Rich](https://rich.readthedocs.io/) • [Textual](https://textual.textualize.io/) • [Pydantic](https://docs.pydantic.dev/)
