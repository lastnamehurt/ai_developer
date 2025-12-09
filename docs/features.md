# aidev Features Overview

A comprehensive guide to all features and capabilities of the AI Developer platform.

## 🎯 Core Systems

### [Profile System](profiles.md)
Switch between pre-configured AI roles instantly. Profiles define MCP servers, environment variables, and tool configurations for different workflows.

**Key Features:**
- Built-in profiles: `web`, `infra`, `qa`, `default`
- Profile inheritance and customization
- Tag-based profile recommendations
- Global and project-specific profiles

**Quick Links:**
- [Profile Management Guide](profiles.md)
- [Creating Custom Profiles](profiles.md#custom-profiles)

---

### [Workflow Orchestration](workflows.md)
Define and execute multi-step AI tasks across different assistants with configurable retries, timeouts, and resumable execution.

**Key Features:**
- Built-in workflows for common tasks (onboarding, documentation, bug triage)
- Multi-assistant coordination (Claude, Codex, Gemini, Cursor)
- Interactive and automated execution modes
- Workflow status tracking and completion marking
- Developer Experience Engineer workflows

**Quick Links:**
- [Workflow System Guide](workflows.md)
- [DX Engineer Workflows](dx-engineer-workflows.md)
- [Creating Custom Workflows](workflows.md#creating-custom-workflows)

---

### [MCP Server Management](mcp_browser.md)
Discover, install, and manage Model Context Protocol (MCP) servers to extend aidev's capabilities.

**Key Features:**
- MCP registry browsing and search
- One-command installation
- Connectivity testing
- Visual TUI browser
- Custom MCP server support

**Quick Links:**
- [MCP Browser Guide](mcp_browser.md)
- [Memory Bank MCP](memory_server_docs.md)

---

### Environment Management
Centralized, encrypted storage for API keys and environment variables with global and project-specific scopes.

**Key Features:**
- Encrypted secret storage
- Global and project-level variables
- Environment variable expansion
- Profile-specific requirements
- Health checks for missing variables

**Commands:**
```bash
ai env set KEY value [--project] [--encrypt]
ai env list
ai env validate
ai env unlock
```

---

### Tool Launcher
Seamlessly launch integrated AI tools (Claude, Cursor, Codex, Gemini, Ollama) with all relevant configurations injected automatically.

**Supported Tools:**
- Claude Code (`ai claude`)
- Cursor (`ai cursor`)
- Codex (`ai codex`)
- Gemini (`ai gemini`)
- Zed (`ai zed`)
- Ollama (`ai ollama`) - Local LLM support

**Features:**
- Automatic MCP config generation
- Profile-aware tool launching
- Environment variable injection
- Tool detection and health checks
- Local-first development with Ollama integration

**Aider Integration:**
- Built-in Aider profile for AI pair programming
- Terminal-first workflow complementing IDE tools
- Git-aware automatic commits
- Works with Ollama for fully local development

👉 **[Aider & Ollama Integration Guide →](aider-ollama-integration.md)**

---

### Smart Quickstart
Automatically detects your project's tech stack and configures an optimal profile and MCP servers.

**Detection:**
- JavaScript/TypeScript (package.json, tsconfig.json)
- Python (pyproject.toml, requirements.txt)
- Docker (Dockerfile, docker-compose.yml)
- Kubernetes (k8s manifests, helm charts)

**Usage:**
```bash
cd your-project
ai quickstart
```

---

### Interactive TUI
Visual terminal interface for configuration management.

**Features:**
- Profile browsing and switching
- MCP server management
- Environment variable editing
- Live configuration previews

**Usage:**
```bash
ai config          # Main configuration TUI
ai mcp browse      # MCP server browser
```

---

### Code Review
Lightweight, heuristic-based code review directly from the CLI.

**Features:**
- Review staged files, all tracked files, or specific files
- External reviewer integration (Aider, Ollama)
- Quick feedback on code quality
- Local LLM support via Ollama for private code review

**Usage:**
```bash
ai review --staged
ai review --all
ai review file1.py file2.py
ai review --staged --provider ollama  # Use local LLM
```

👉 **[Aider & Ollama Integration Guide →](aider-ollama-integration.md)**

---

### Health Checks
Diagnose common setup issues with actionable fixes.

**Checks:**
- Tool binary availability
- Required environment variables
- MCP server connectivity
- Profile configuration validity

**Usage:**
```bash
ai doctor
```

---

### Backup & Restore
Easily migrate your aidev configuration between machines.

**Features:**
- Complete configuration backup (profiles, env vars, MCP configs)
- Encrypted secrets preservation
- One-command restore

**Usage:**
```bash
ai backup --output backup.tar.gz
ai restore backup.tar.gz
```

---

## 🔧 Advanced Features

### Git Integration
- Branch synchronization workflow (`sync_branch`)
- Git MCP server for repository operations
- Workflow integration with GitLab/GitHub

### Machine Migration
- Configuration backup/restore
- Cross-platform compatibility
- Encrypted secrets migration

### Custom Profiles
- Profile inheritance
- Profile cloning and sharing
- Tag-based recommendations

### Project-Specific Configuration
- Per-project profiles
- Project-level environment variables
- Project workflow definitions

---

## 📚 Documentation Index

- [Architecture](architecture.md) - System design and internals
- [Commands Reference](commands.md) - Complete command reference
- [Profiles Guide](profiles.md) - Profile system deep dive
- [Workflows Guide](workflows.md) - Workflow orchestration
- [MCP Browser](mcp_browser.md) - MCP server management
- [Memory Bank](memory_server_docs.md) - Persistent project memory
- [DX Engineer Workflows](dx-engineer-workflows.md) - Specialized workflows
- [Aider & Ollama Integration](aider-ollama-integration.md) - Local-first AI development

---

## 🚀 Getting Started

1. **Install**: `pipx install "git+https://github.com/lastnamehurt/ai_developer.git@main"`
2. **Setup**: `ai setup`
3. **Quickstart**: `cd your-project && ai quickstart`
4. **Launch**: `ai claude` or `ai cursor`

See the [README](../README.md) for detailed installation and setup instructions.
