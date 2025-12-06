# Reference: Original AI Developer Tool (Company Version)

> This is a reference document from the company-built version. We're using this as inspiration for a universal, personal project rebuild.

# 🤖 AI Development Environment

Universal AI Development Environment launcher with **profile-based MCP configurations** that provides consistent API access across all AI tools (Cursor, Claude Code, and other AI-powered IDEs).

## 🚀 Quick Start

### Installation
```bash
# One-line installation
git clone --depth 1 git@gitlab.checkrhq.net:foundations/delivery-platform/dev-productivity/ai-developer.git /tmp/ai-dev-install && cd /tmp/ai-dev-install && ./install.sh && cd - && rm -rf /tmp/ai-dev-install
```

### First Use
```bash
# 1. Configure your AI development credentials
ai setup

# 2. Navigate to any project and initialize
cd my-project
ai init

# 3. Launch your favorite AI tools with profiles
ai cursor                     # Cursor (default profile)
ai cursor --profile devops    # Cursor with GitLab write access + K8s
ai claude --profile persistent # Claude Code with memory (also supported)

# 4. Stay up to date
ai install                    # Updates to the latest version
```

## 📚 Documentation

### Getting Started
- **[Complete Onboarding Guide](docs/onboarding-guide.md)** - Step-by-step setup for new users
- **[Profile System Guide](docs/profile-system-guide.md)** - Understanding and using AI profiles
- **[Engineering Workflow](docs/engineering-workflow.md)** - Built-in development workflows

### Core Features
- **[Features Overview](docs/features.md)** - Complete feature list and capabilities
- **[Architecture Guide](docs/ai-developer-architecture.md)** - Technical architecture and design
- **[Memory Persistence](docs/memory-persistence-system.md)** - Cross-session context preservation
- **[Telemetry System](docs/telemetry.md)** - Privacy-first usage analytics (opt-in)

### Advanced Usage
- **[Claude Sub Agents](docs/claude-sub-agents-guide.md)** - Specialized workflow assistants
- **[MCP Server Development](docs/mcp-server-development-framework.md)** - Creating custom integrations
- **[Testing Guide](docs/testing-system-guide.md)** - Running and writing tests

### Workflow Integration
- **[Engineering Workflow Integration](docs/engineering-workflow-integration.md)** - Automated workflow setup

## 🎯 Supported Tools & Profiles

| Tool | Command | Description |
|------|---------|-------------|
| Cursor | `ai cursor [--profile <name>]` | Launch Cursor with profile-specific MCP config |
| Cursor App | `ai cursor-app [--profile <name>]` | Launch Cursor app with full editor |
| Claude Code | `ai claude [--profile <name>]` | Launch Claude Code (also supported) |
| Claude Desktop | `ai claude-app [--profile <name>]` | Launch Claude Desktop app (also supported) |

### Available Profiles

| Profile | Use Case | Key Tools |
|---------|----------|-----------|
| **default** | Daily development | Filesystem, Git, JIRA |
| **persistent** | Long-term projects | Memory, context preservation |
| **devops** | Infrastructure | GitLab (RW), Kubernetes |
| **qa** | Testing & QA | GitLab (RO), Cypress, test analysis |
| **research** | Investigation | Web search, memory, documentation |

## 🔧 Essential Commands

### Setup & Management
```bash
ai setup                   # Configure AI development credentials
ai init                    # Initialize project with AI tools
ai check                   # Verify environment setup
ai install                 # Update to latest version
```

### AI Tools
```bash
ai cursor                  # Launch Cursor (default profile)
ai cursor --profile devops # Launch Cursor (devops profile)
ai cursor --profile qa     # Launch Cursor (qa profile)
ai claude --profile persistent # Also works with Claude Code
```

### Environment Management
```bash
ai load                    # Load and display environment variables
ai env-sync                # Sync local .env values to AI environment
```

### Telemetry (Optional)
```bash
ai telemetry status        # Check telemetry configuration
ai telemetry enable        # Enable usage analytics (opt-in)
ai telemetry disable       # Disable telemetry
ai telemetry export        # Export data for review
```

## 🌍 Environment Variables

The tool uses a **single environment file** (`~/.local/ai-dev/.env`) with variable expansion:

### Required for GitLab Profiles
```bash
GITLAB_PERSONAL_ACCESS_TOKEN=your-token
GITLAB_API_URL=https://gitlab.checkrhq.net/api/v4  # Defaults to checkrhq gitlab
```

### Optional Configuration
```bash
# Git Configuration
GIT_AUTHOR_NAME="Your Name"
GIT_AUTHOR_EMAIL="your-email@company.com"

# Memory Bank (persistent profile)
MEMORY_BANK_ROOT=${HOME}/.local/ai-dev/memory-banks

# Kubernetes (devops profile)
KUBECONFIG=${HOME}/.kube/config
```

## 🏗 How It Works

1. **Global Installation**: Installs `ai` command to `~/.local/ai-dev/bin`
2. **Project Initialization**: `ai init` creates project-specific configs
3. **Environment Loading**: Automatically loads `.env` when launching tools
4. **MCP Configuration**: Shares global MCP servers across all AI tools
5. **Tool Integration**: Launches tools with full environment context

## 🧪 Testing

```bash
# Run all tests
./tests/run-tests.sh

# Run specific test suites
./tests/run-tests.sh utils        # Utility functions (no setup required)
./tests/run-tests.sh core         # Core functionality (requires ./install.sh)
./tests/run-tests.sh integration  # Full integration (requires credentials)
```

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Adding new MCP servers and integrations
- Creating custom MCP servers
- Testing procedures and workflow
- Code style guidelines

## 🚨 Troubleshooting

### Command not found: ai
```bash
# Check PATH and add if missing
echo 'export PATH="$HOME/.local/ai-dev/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Environment variables not loading
```bash
# Check setup and test loading
ai check
ai load
```

### AI tools not recognizing APIs
```bash
# Verify MCP configuration
ai check
cat ~/.local/ai-dev/mcp.json
```

---

**Need help?** Check the [Complete Onboarding Guide](docs/onboarding-guide.md) or run `ai help` for interactive guidance.
