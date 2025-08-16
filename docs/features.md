# AI Developer Features

The AI Developer tool provides a comprehensive suite of features for standardizing AI development environments across teams and projects.

## Core Features

### 🚀 Installation & Setup
- **One-Command Installation**: Single command installs entire AI development environment
- **Multi-Mode Installation**: Supports both local files and remote GitLab repository installation
- **Automatic CLI Detection**: Auto-installs Claude CLI and Cursor CLI with fallback methods
- **Cross-Platform Support**: Works on macOS, Linux, and Windows (WSL/Git Bash)
- **PATH Integration**: Automatically adds `ai` command to system PATH

### 🔧 Profile-Based MCP Architecture
- **5 Pre-Configured Profiles**: default, persistent, devops, qa, research
- **DRY Base Layer System**: Reusable components (common, conversational, persistent)
- **Profile Matrix**: Each profile combines base layers + additional servers
- **Dynamic Profile Selection**: Switch profiles per tool launch with `--profile` flag

### 🛠 Universal AI Tool Launcher
- **Claude Code Integration**: `ai claude` with profile-specific MCP configs
- **Claude Desktop Support**: `ai claude-app` for alternative Claude desktop app
- **Cursor CLI Integration**: `ai cursor` launches cursor-agent with MCP integration
- **Cursor App Support**: `ai cursor-app` launches full Cursor editor with GUI
- **Cross-Tool Consistency**: Same MCP servers work across all AI tools

### 🌐 Environment Management
- **Centralized Credentials**: Single `~/.local/ai-dev/.env` file for all profiles
- **Variable Expansion**: `${VARIABLE}` placeholders expanded at runtime
- **Local Override Support**: Project-specific `.env` files override global variables
- **Smart Environment Sync**: `ai env-sync` automatically updates credentials
- **Backup Protection**: Creates backups before credential updates
- **Pattern Recognition**: Automatically finds and updates placeholder values

### 📋 Project Initialization
- **Zero-Config Setup**: `ai init` auto-configures any project for AI development
- **Engineering Workflow Integration**: Built-in JIRA workflows and Git standards
- **Claude Sub Agents**: Specialized workflow assistants (devops, qa, review, research)
- **Cursor Rules Generation**: Auto-configures `.cursor/rules.json` for CLAUDE.md
- **Template Processing**: Copies engineering workflow templates to projects

### 🔌 MCP Server Integration
- **GitLab Integration**: Repository access, issues, merge requests (read/write modes)
- **Atlassian Integration**: JIRA tickets and Confluence pages
- **Filesystem Operations**: File and directory management
- **Git Operations**: Repository information and version control
- **Memory Bank**: Persistent AI memory across sessions
- **Web Search**: DuckDuckGo search integration
- **Sequential Thinking**: Step-by-step reasoning and planning
- **Kubernetes**: Cluster operations and management
- **Testing Tools**: Cypress and test overlap analysis

### 🤖 Claude Sub Agents
- **devops-deployer**: Kubernetes and GitLab deployment specialist
- **qa-test-runner**: E2E/API test execution and coverage analysis
- **core-dev-reviewer**: Security-focused code review with memory
- **research-synthesizer**: External research and documentation synthesis
- **Separate Context Windows**: Keep specialized tasks out of main conversation
- **Auto-Delegation**: Claude automatically routes tasks to appropriate agents
- **Version Controlled**: Agents stored per-project in `.claude/agents/`

### 📊 Engineering Workflow Features
- **JIRA Integration**: Automated ticket creation, status updates, linking
- **Git Workflow Standards**: Branch naming (JIRA-###-description), commit patterns
- **Conventional Commits**: Standardized commit message format
- **Merge Request Templates**: Automated MR creation with proper formatting
- **Documentation Standards**: Consistent project documentation approach
- **Testing Guidelines**: Quality assurance workflow integration
- **Problem Analysis**: AI-guided research and ticket creation

### 🔄 Maintenance & Updates
- **Self-Updating**: `ai install` updates from GitLab repository automatically
- **Environment Verification**: `ai check` validates setup and configuration
- **Credential Management**: `ai setup` provides guided credential configuration
- **Variable Loading**: `ai load` displays all loaded environment variables
- **Config Synchronization**: `ai sync` syncs Claude configs to Cursor format

### 🏗 Architecture Features
- **Global Configuration**: Centralized setup in `~/.local/ai-dev/`
- **Symlinked Configs**: Project configs link to global profiles
- **Template-Driven**: Distribution-friendly templates with variable substitution
- **Modular Design**: Separate utility, core, and project management modules
- **Error Handling**: Graceful degradation and comprehensive logging
- **Shell Compatibility**: Works across bash, zsh, and POSIX environments

### 📈 Development Productivity
- **Consistent Workflows**: Same engineering standards across all projects
- **Context-Aware AI**: Tools understand project structure and standards
- **Multiple Project Support**: Global setup works across unlimited projects
- **Profile Flexibility**: Choose appropriate tool configuration per task
- **Memory Persistence**: Long-term project knowledge with persistent profiles
- **Cross-Tool Memory**: Sub agents maintain state across sessions

## Profile Details

### Available Profiles

| Profile | Base Layers | Additional Servers | Use Case |
|---------|-------------|-------------------|----------|
| **default** | common | atlassian | Basic development with JIRA integration |
| **persistent** | common + conversational + persistent | - | Long-term projects with memory across sessions |
| **devops** | common + conversational | gitlab (RW), k8s | GitLab write access, Kubernetes operations |
| **qa** | common + conversational | gitlab (RO), cypress, test-analyzer | Testing tools with GitLab read access |
| **research** | common + conversational + persistent | duckduckgo, compass, sequentialthinking | Web search and information gathering with memory |

### Base Layers

- **common**: Core tools (filesystem, git) - included in all profiles
- **conversational**: Serena conversational AI - included in most profiles
- **persistent**: Memory-bank for cross-session persistence

## Command Reference

### Installation & Updates
```bash
ai install                 # Install/update the AI development environment
ai setup                   # Configure your AI development credentials
```

### Project Management
```bash
ai init                    # Initialize project with AI tools
ai check                   # Verify environment setup
ai load                    # Load env vars to current shell
ai sync                    # Sync Claude configs to Cursor format
ai env-sync                # Update AI Environment with local values
```

### AI Tools
```bash
ai claude                  # Launch Claude Code (default profile)
ai claude --profile persistent # Launch Claude Code (persistent profile)
ai claude-app             # Launch Claude Desktop app (default profile)
ai cursor                  # Launch Cursor CLI (default profile)
ai cursor --profile qa     # Launch Cursor CLI (qa profile)
ai cursor-app              # Launch Cursor app (default profile)
```

### Profile Management
```bash
ai help                    # Show all available profiles and commands
ai check                   # Verify environment and profile setup
ai setup                   # Configure credentials (guided setup)
```

## Benefits

### 🚀 **Productivity & Efficiency**
- ✅ **Consistent workflows** across all projects and team members
- ✅ **Automated JIRA integration** - tickets created and updated automatically
- ✅ **Standardized Git practices** - branch naming, commit messages, MR templates
- ✅ **Quality assurance** - built-in testing and review processes
- ✅ **Knowledge sharing** - workflows captured and reusable

### 🎯 **AI Tool Enhancement**
- ✅ **Context-aware AI** - tools understand your project structure and standards
- ✅ **Automated guidance** - AI follows established workflows without manual prompting
- ✅ **Integrated tooling** - seamless switching between different AI tools and profiles
- ✅ **Project consistency** - same workflows and standards across all AI interactions

### 🔧 **Developer Experience**
- ✅ **Zero configuration** - works out of the box with `ai init`
- ✅ **Profile flexibility** - choose the right tool configuration for each task
- ✅ **Environment management** - automatic credential loading and synchronization
- ✅ **Workflow templates** - pre-built processes for common development tasks

This comprehensive feature set makes the AI Developer tool a complete solution for standardizing AI development environments across teams and projects.