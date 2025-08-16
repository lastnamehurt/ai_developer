# 🚀 AI Development Environment - Quick Start

Get Claude Code and Cursor set up with powerful AI development tools in 3 simple steps.

## ⚡ 3-Step Setup

### 1. Install
```bash
# One-line installation
git clone --depth 1 git@github.com:lastnamehurt/ai_developer.git /tmp/ai-dev-install && cd /tmp/ai-dev-install && ./install.sh && cd - && rm -rf /tmp/ai-dev-install

# Or manual installation
git clone git@github.com:lastnamehurt/ai_developer.git
cd ai-developer
./install.sh
```

### 2. Configure Credentials
```bash
ai setup  # Opens your credentials file for editing
```
Add your API tokens for GitLab, JIRA, etc.

### 3. Use in Any Project
```bash
cd my-project
ai init                    # Set up project configs
ai claude                  # Launch Claude Code
ai cursor-app              # Launch Cursor app
```

## 🎯 What You Get

### AI Tools with Full MCP Support
- **Claude Code** (`ai claude`) - Desktop app with full MCP integration
- **Claude Desktop** (`ai claude-app`) - Alternative Claude desktop app  
- **Cursor CLI** (`ai cursor`) - Terminal automation via cursor-agent
- **Cursor App** (`ai cursor-app`) - Full Cursor editor with GUI

### Built-in Integrations
- 📊 **GitLab** - Issues, MRs, repositories
- 🏗️ **JIRA/Confluence** - Tickets, documentation
- 📁 **File System** - Project operations
- 🔍 **Git** - Repository management
- 💾 **Memory Bank** - Persistent AI memory
- 🔍 **Web Search** - Real-time information

### Multiple Profiles for Different Workflows
- `ai claude --profile persistent` - Memory across sessions
- `ai cursor --profile devops` - GitLab + Kubernetes tools
- `ai claude --profile qa` - Testing and validation tools
- `ai cursor-app --profile research` - Web search + memory

## 🛠 Common Workflows

### Daily Development
```bash
cd my-project
ai claude --profile persistent  # Long-term project memory
ai cursor-app                   # Visual development
```

### DevOps & Deployment
```bash
ai claude --profile devops      # GitLab write + K8s access
ai cursor --profile devops      # CLI automation
```

### Quality Assurance
```bash
ai claude --profile qa          # Testing tools + GitLab read
ai cursor --profile qa          # Automated test execution
```

### Research & Planning
```bash
ai claude --profile research    # Web search + memory
ai cursor-app --profile research # GUI with research tools
```

## 💡 Pro Tips

- **CLI vs App**: Use `ai cursor` for automation, `ai cursor-app` for visual editing
- **Memory**: `persistent` and `research` profiles remember across sessions
- **Environment**: Global credentials in `~/.local/ai-dev/.env`, project overrides in local `.env`
- **Profiles**: Switch profiles for different tool sets - no need to reconfigure
- **Updates**: Run `ai install` anytime to get the latest features

## 📚 Learn More

- [README.md](./README.md) - Full documentation and examples
- [Architecture](./docs/ai-developer-architecture.md) - How it all works
- [Engineering Workflow](./docs/engineering-workflow.md) - Built-in development standards

## 🆘 Need Help?

```bash
ai help     # Show all commands and profiles
ai check    # Verify your setup
```

Ready to supercharge your development workflow! 🚀