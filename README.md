# 🤖 AI Development Environment

Universal AI Development Environment launcher with **profile-based MCP configurations** that provides consistent API access across all AI tools (Claude Code, Cursor, and other IDEs with extensions).

## 🚀 Quick Start

### Installation

**One-line Installation**
```bash
# Quick install (tries SSH first, then HTTPS)
git clone --depth 1 git@gitlab.checkrhq.net:foundations/delivery-platform/dev-productivity/ai-developer.git /tmp/ai-dev-install && cd /tmp/ai-dev-install && ./install.sh && cd - && rm -rf /tmp/ai-dev-install
```

**Manual Installation (if one-liner fails)**
```bash
git clone git@gitlab.checkrhq.net:foundations/delivery-platform/dev-productivity/ai-developer.git
cd ai-developer
./install.sh
```

### First Use

```bash
# 1. Installation is complete! The ai command is now available globally

# 2. Configure your AI development credentials
ai setup

# 3. Navigate to any project
cd my-project

# 4. Initialize AI development environment
ai init

# 5. Create CLAUDE.md (manual step - configs already synced!)
# Open Claude and run: /init

# 6. Launch your favorite AI tools with profiles
ai claude                     # Claude Code (default profile)
ai claude-app                 # Claude Desktop app (default profile)
ai cursor                     # Cursor CLI (cursor-agent) (default profile)
ai cursor-app                 # Cursor app (default profile)
ai cursor --profile devops    # Cursor CLI with GitLab write access
# Other IDEs: Launch directly - extensions read the same configs!

# 7. Stay up to date (run from anywhere)
ai install     # Updates to the latest version

# 8. Optional: Update AI Environment with local values
ai env-sync                # Copy local .env values to AI Environment
```

## 📋 Engineering Workflow Integration

The AI environment automatically sets up a standardized engineering workflow that helps AI tools understand how to complete tasks using JIRA, Git branching, and merge requests.

### How It Works

When you run `ai init`, the following files are created:

- **`.claude/engineering-workflow.md`** - Complete workflow documentation with JIRA integration, branching patterns, and MR creation
- **`CLAUDE.local.md`** - Local instruction file with engineering workflow reference (not committed to version control)
- **`.cursor/rules.json`** - Cursor configuration that summarizes both workflow and project instructions

### File Structure

```
your-project/
├── CLAUDE.md                           # Your project instructions (created by Claude /init command)
├── CLAUDE.local.md                     # Local workflow reference (auto-created)
├── .claude/
│   ├── .mcp.json → ~/.local/ai-dev/mcp.json  # Symlinked MCP config
│   ├── engineering-workflow.md         # Complete engineering workflow
│   └── agents/                         # Claude Sub Agents (version controlled)
│       ├── devops-deployer.md          # Deployment specialist
│       ├── qa-test-runner.md           # Testing workflow agent
│       ├── core-dev-reviewer.md        # Code review agent
│       └── research-synthesizer.md     # Research and documentation agent
└── .cursor/
    ├── mcp.json → ~/.local/ai-dev/mcp.json   # Symlinked MCP config  
    └── rules.json                       # Summarizes CLAUDE.md, CLAUDE.local.md, and workflow
```

### Benefits

✅ **Resilient**: Engineering workflow survives even if `CLAUDE.md` is recreated by Claude Code  
✅ **Consistent**: Both Claude Code and Cursor see the same workflow instructions  
✅ **Local**: `CLAUDE.local.md` stays local and doesn't interfere with your team's `CLAUDE.md`  
✅ **Automatic**: No manual setup - works immediately after `ai init`

## ✨ Features

- **Profile-Based MCP**: 5 pre-configured profiles for different use cases
- **Universal Launcher**: One `ai` command for all AI tools with profile support
- **Claude Sub Agents**: Specialized workflow assistants for deployment, QA, code review, and research
- **Single Environment File**: Centralized `~/.local/ai-dev/.env` with variable expansion
- **Self-Updating**: `ai install` updates from GitLab automatically
- **Environment Management**: Automatic loading of API credentials
- **MCP Integration**: Consistent API access (GitLab, Atlassian, etc.)
- **Claude Integration**: Smart Claude /init workflow with config synchronization
- **Cursor Rules**: Auto-configures `.cursor/rules.json` to summarize `CLAUDE.md`
- **Engineering Workflow Templates**: Built-in engineering task workflows and JIRA integration
- **Environment Variable Flexibility**: Easy synchronization between local and AI Environment variables
- **Cross-Platform**: Works on macOS, Linux, and Windows (WSL/Git Bash)
- **Claude & Cursor CLI Integration**: Automatic installation of both Claude CLI and Cursor CLI for seamless development

## 🎯 Supported Tools & Profiles

| Tool | Command | Description |
|------|---------|-------------|
| Claude Code | `ai claude [--profile <name>]` | Launch Claude Code (preferred) with profile-specific MCP config |
| Claude Desktop | `ai claude-app [--profile <name>]` | Launch Claude Desktop app with profile-specific MCP config |
| Cursor CLI | `ai cursor [--profile <name>]` | Launch Cursor CLI (cursor-agent) with profile-specific MCP config |
| Cursor App | `ai cursor-app [--profile <name>]` | Launch Cursor app with profile-specific MCP config |
| Other IDEs | Launch directly | Extensions read the same configs |

**Tool Selection:**
- **Claude Code** (`ai claude`) - Desktop app with full MCP support (recommended)
- **Claude Desktop** (`ai claude-app`) - Alternative Claude desktop app
- **Cursor CLI** (`ai cursor`) - Terminal-based Cursor agent for automation
- **Cursor App** (`ai cursor-app`) - Full Cursor editor with GUI

### 📋 Available Profiles

Built using a **DRY base layer architecture** for consistent tool availability:

**Base Layers:**
- **common**: Core tools (filesystem, git) - included in all profiles
- **conversational**: Serena conversational AI - included in most profiles  
- **persistent**: Memory-bank for cross-session persistence

**Profile Matrix:**

| Profile | Base Layers | Additional Servers | Use Case |
|---------|-------------|-------------------|----------|
| **default** | common | atlassian | Basic development with JIRA integration |
| **persistent** | common + conversational + persistent | - | Long-term projects with memory across sessions |
| **devops** | common + conversational | gitlab (RW), k8s | GitLab write access, Kubernetes operations |
| **qa** | common + conversational | gitlab (RO), cypress, test-analyzer | Testing tools with GitLab read access |
| **research** | common + conversational + persistent | duckduckgo, compass, sequentialthinking | Web search and information gathering with memory |

### 🤖 Claude Sub Agents

The system includes **Claude Sub Agents** - specialized workflow assistants that work on top of your MCP profiles:

| Agent | Purpose | Best Used With | Description |
|-------|---------|----------------|-------------|
| **devops-deployer** | Deployment & Operations | `devops` profile | Kubernetes and GitLab deployment specialist with safety checks |
| **qa-test-runner** | Testing & QA | `qa` profile | E2E/API test execution and coverage analysis |
| **core-dev-reviewer** | Code Review | `persistent` profile | Security-focused code review with memory of standards |
| **research-synthesizer** | Research & Documentation | `research` profile | External research and documentation synthesis |

**How Sub Agents Work:**
- 🧠 **Separate context windows** keep noisy tasks out of your main conversation
- 🔧 **Inherit MCP tools** from your active profile automatically  
- 📝 **Persistent state** via memory-bank integration for continuity
- 🎯 **Auto-delegation** - Claude routes tasks to appropriate agents
- 📋 **Version controlled** - agents stored in `.claude/agents/` per project

## 🔧 Commands

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
# Other IDEs: Launch directly - extensions handle MCP configs
```

### Profile Management
```bash
ai help                    # Show all available profiles and commands
ai check                   # Verify environment and profile setup
ai setup                   # Configure credentials (guided setup)
```

## 🌍 Environment Variables & Profile Requirements

The tool uses a **single environment file** (`~/.local/ai-dev/.env`) with variable expansion for all profiles:

### Required for GitLab Profiles (repo-ops, qa)
```bash
GITLAB_PERSONAL_ACCESS_TOKEN=your-token
GITLAB_API_URL=https://gitlab.com/api/v4  # Defaults to gitlab.com
```

### Optional Configuration
```bash
# Git Configuration
GIT_AUTHOR_NAME="Your Name"
GIT_AUTHOR_EMAIL="your-email@company.com"

# Memory Bank (core-dev profile)
MEMORY_BANK_ROOT=${HOME}/.local/ai-dev/memory-banks  # Default location

# Kubernetes (repo-ops profile)  
KUBECONFIG=${HOME}/.kube/config  # Default location
```

### Profile-Specific Variables
- **default**: No special requirements
- **persistent**: Optional memory bank storage location
- **devops**: Requires GitLab token, optional Kubernetes config
- **qa**: Requires GitLab token (read-only mode)
- **research**: Optional memory bank storage location

## 🔄 Centralized Environment Management

### AI Environment Variables

The `ai` command now supports **centralized environment variable management** to eliminate the need to copy/paste credentials into each project.

### MCP Configuration with Variable Substitution

The `ai init` command now processes MCP templates with **automatic variable substitution** to ensure MCP servers work correctly with your credentials.

#### How MCP Variable Substitution Works

1. **Template Processing**: `ai init` processes the MCP template with environment variable substitution
2. **Two Methods**: Uses `envsubst` if available, falls back to `sed` for compatibility
3. **Distribution-Friendly**: Templates use `${VAR}` placeholders for distribution
4. **Personal Credentials**: Your AI Environment variables are automatically substituted

#### Supported MCP Servers

- **GitLab**: Access repositories, issues, merge requests
- **Atlassian**: Jira tickets and Confluence pages
- **Filesystem**: File and directory operations
- **Git**: Repository information and operations

#### MCP Variable Substitution Examples

```bash
# Template (distribution-friendly)
"GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}"

# Processed (with your credentials)
"GITLAB_PERSONAL_ACCESS_TOKEN": "your-actual-token-here"
```

#### Benefits

- ✅ **No more MCP connection issues** - Variables properly substituted
- ✅ **Distribution-friendly** - Templates use placeholders
- ✅ **Automatic processing** - `ai init` handles variable substitution
- ✅ **Fallback support** - Works with or without `envsubst`
- ✅ **Consistent across tools** - Same MCP config for Claude Code and Cursor

### 🔄 Flexible Environment Variable Updates

The AI development environment now includes a **smart environment variable synchronization tool** that makes it easy to keep your AI Environment credentials up to date.

#### Sync Environment Variables Command

The `ai env-sync` command automatically detects and updates your AI Environment file with values from local `.env` files or existing environment variables.

**Features:**
- 🔍 **Smart Detection**: Automatically finds variables from local `.env` files or current environment
- 🛡️ **Safe Updates**: Creates backups before making changes
- 🔄 **Pattern Matching**: Intelligently matches placeholder patterns in AI Environment files
- 📊 **Progress Tracking**: Shows exactly what was updated and what wasn't
- 💾 **Backup Protection**: Always creates a backup before making changes

**Usage:**
```bash
# From any project directory with a .env file
ai env-sync

# Or specify a custom local .env file
LOCAL_ENV_FILE=my-custom.env ai env-sync

# From the ai-dev installation directory
cd ~/.local/ai-dev
ai env-sync
```

**What It Does:**
1. **Scans Sources**: Checks local `.env` files and current environment variables
2. **Pattern Matching**: Finds placeholder patterns like `your-gitlab-token-here` in AI Environment files
3. **Safe Updates**: Replaces placeholders with actual values while preserving file format
4. **Backup Creation**: Creates `.backup` files before making any changes
5. **Progress Report**: Shows summary of successful updates and any issues

**Supported Variable Sources:**
- Local `.env` files in current directory
- Currently set environment variables
- Common credential variables (GitLab, DataDog, Atlassian, etc.)

**Example Output:**
```bash
$ ai env-sync
🔄 Updating AI Environment with available values while preserving format...
💾 Backup created: /Users/username/.local/ai-dev/.env.backup
🔍 Collecting variables from available sources...
📥 Loading variables from .env...
📊 Found 8 variables in .env
🔄 Updating AI Environment file with available values...
✅ Updated GITLAB_TOKEN
✅ Updated GIT_AUTHOR_NAME
⚠️  No placeholder found for CUSTOM_VAR

📊 Update Summary:
  ✅ Successfully updated: 2 variables
  💾 Backup saved as: /Users/username/.local/ai-dev/.env.backup
  📊 Updated file: /Users/username/.local/ai-dev/.env
```

#### How It Works

1. **AI Environment File**: `~/.local/ai-dev/.env` contains all shared credentials
2. **Automatic Loading**: Every `ai` command loads both AI Environment and local variables
3. **Local Override**: Project-specific `.env` files can override AI Environment variables
4. **No More Copy/Paste**: Set up once, use everywhere
5. **Easy Updates**: Use `ai env-sync` to sync new credentials

#### Setup

```bash
# Configure with guided setup:
ai setup

# Or manually edit:
~/.local/ai-dev/.env

# Example .env content:
GITLAB_PERSONAL_ACCESS_TOKEN=your-gitlab-token-here
# ... all your shared credentials
```

#### Usage

**For new projects:**
```bash
cd /path/to/new/project
ai init                    # Global variables automatically available
ai claude                  # or ai cursor
```

**For existing projects:**
```bash
cd /path/to/existing/project
ai claude                  # Global variables loaded automatically
```

**Check what's loaded:**
```bash
ai load                    # Load and display all variables
ai check                   # Verify environment setup
```

**Update global credentials:**
```bash
# From a project with updated .env file
ai env-sync

# Or from the ai-dev installation
cd ~/.local/ai-dev
ai env-sync
```

#### Benefits

- ✅ **No more copy/paste** - Global variables available in every project
- ✅ **Secure** - Global file in home directory, not committed to repos
- ✅ **Flexible** - Local `.env` can override global variables
- ✅ **Automatic** - No manual setup required for new projects
- ✅ **Centralized** - Update credentials in one place
- ✅ **Smart Updates** - Use `ai env-sync` to sync new credentials
- ✅ **Backup Protection** - Always safe with automatic backups
- ✅ **Pattern Recognition** - Automatically finds and updates placeholder values

## 🎯 Engineering Workflow Integration

The AI development environment includes **built-in engineering workflow templates** that automatically guide AI tools through standard development tasks.

### What's Included

- **📋 Engineering Task Workflow**: Complete workflow from problem analysis to delivery
- **🎫 JIRA Integration**: Automated ticket creation, status updates, and linking
- **🔄 Git Workflow**: Branch naming, commit messages, and merge request templates
- **📝 Documentation Standards**: Consistent project documentation and code comments
- **🧪 Testing Guidelines**: Test planning and quality assurance workflows

### How It Works

The engineering workflow integration follows this smart approach:

1. **🔄 Flexible Integration**: Works with existing CLAUDE.md files or new projects
2. **📄 Reference Template**: Copies `engineering-workflow.md` as a standalone reference
3. **🤝 Automatic Merging**: If CLAUDE.md exists, the workflow gets appended automatically
4. **⚙️ AI Tool Configuration**: Both files are configured for AI context via `.cursor/rules.json`

### Usage Examples

**New Project:**
```bash
cd new-project
ai init                    # Sets up configs & copies engineering-workflow.md template
ai claude                  # Launch Claude Code
# In Claude Code: use '/init' command to create CLAUDE.md
ai init                    # Auto-detects CLAUDE.md and integrates workflow (one command!)
```

**Existing Project with CLAUDE.md:**
```bash
cd existing-project        # Has CLAUDE.md already
ai init                    # Auto-detects and integrates workflow into existing CLAUDE.md
```

**AI Interaction:**
```bash
# Now ask your AI tool:
# "Create a JIRA ticket for implementing user authentication"
# "Help me follow the engineering workflow for this bug fix"
# "Review my code changes according to our standards"
```

### Benefits

#### 🚀 **Productivity & Efficiency**
- ✅ **Consistent workflows** across all projects and team members
- ✅ **Automated JIRA integration** - tickets created and updated automatically
- ✅ **Standardized Git practices** - branch naming, commit messages, MR templates
- ✅ **Quality assurance** - built-in testing and review processes
- ✅ **Knowledge sharing** - workflows captured and reusable

#### 🎯 **AI Tool Enhancement**
- ✅ **Context-aware AI** - tools understand your project structure and standards
- ✅ **Automated guidance** - AI follows established workflows without manual prompting
- ✅ **Integrated tooling** - seamless switching between different AI tools and profiles
- ✅ **Project consistency** - same workflows and standards across all AI interactions

#### 🔧 **Developer Experience**
- ✅ **Zero configuration** - works out of the box with `ai init`
- ✅ **Profile flexibility** - choose the right tool configuration for each task
- ✅ **Environment management** - automatic credential loading and synchronization
- ✅ **Workflow templates** - pre-built processes for common development tasks

### Workflow Features

| Feature | Description |
|---------|-------------|
| **Problem Analysis** | AI-guided research and JIRA ticket creation |
| **Implementation Planning** | TodoWrite integration for task breakdown |
| **Git Branch Management** | Standardized branch naming (JIRA-###-description) |
| **Commit Standards** | Conventional Commits format with JIRA linking |
| **Code Review Process** | MR templates and review checklists |
| **Status Tracking** | Automatic JIRA status transitions |

#### Variable Loading Order

1. **Global variables** from `~/.local/ai-dev/.env` (loaded first)
2. **Local variables** from project's `.env` file (overrides global)
3. **Total count** displayed when loading (e.g., "Loaded 58 environment variables")

#### Example Output

```bash
$ ai load
ℹ️  Loading shared AI environment variables from /Users/username/.local/ai-dev/.env
✅ Loaded 18 shared AI environment variables
ℹ️  Loading local environment variables from /path/to/project/.env
✅ Loaded 40 local environment variables
✅ Total: Loaded 58 environment variables (global + local)
```

## 🏗 How It Works

1. **Global Installation**: Installs `ai` command to `~/.local/ai-dev/bin`
2. **Project Initialization**: `ai init` creates project-specific configs
3. **Environment Loading**: Automatically loads `.env` when launching tools
4. **MCP Configuration**: Shares global MCP servers across all AI tools
5. **Tool Integration**: Launches tools with full environment context

## 📁 File Structure

After installation:

```
~/.local/ai-dev/                    # Global configuration
├── mcp.json → mcp-profiles/default.mcp.json  # Symlink to default profile
├── .env                            # Single environment file with variable expansion
├── bin/ai                          # Profile-aware launcher
├── mcp-layers/                     # DRY base layer architecture
│   ├── base.common.json           # Core tools (filesystem, git)
│   ├── base.conversational.json   # Serena conversational AI
│   └── base.persistent.json       # Memory-bank for persistence
└── mcp-profiles/                   # Profile configurations using base layers
    ├── default.mcp.json            # layers: [common] + atlassian
    ├── persistent.mcp.json         # layers: [common, conversational, persistent]
    ├── devops.mcp.json             # layers: [common, conversational] + gitlab (RW), k8s
    ├── qa.mcp.json                 # layers: [common, conversational] + gitlab (RO), cypress, test-analyzer
    └── research.mcp.json           # layers: [common, conversational, persistent] + search tools

your-project/             # Project-specific files (created by ai init)
├── .env                  # Local API credentials (optional, overrides global)
├── .cursor/
│   └── rules.json        # Auto-configured for CLAUDE.md
└── CLAUDE.md            # Created by Claude /init command
```

### Profile Resolution
- `ai claude` → uses `~/.local/ai-dev/mcp-profiles/default.mcp.json` 
- `ai claude --profile persistent` → uses `~/.local/ai-dev/mcp-profiles/persistent.mcp.json`
- Variables like `${GITLAB_PERSONAL_ACCESS_TOKEN}` are expanded using `envsubst`

## 🔄 What `ai init` Does

1. **Creates `.cursor/rules.json`** configured for basic file inclusion/exclusion
2. **Sets up engineering workflow** if templates are available  
3. **No MCP config creation** - profiles are managed globally
4. **Provides setup guidance** for using Claude Code and Cursor with profiles

### Profile-Based Changes
- **No per-project MCP configs** - all profiles live in `~/.local/ai-dev/mcp-profiles/`
- **Global environment** - single `~/.local/ai-dev/.env` file for all profiles
- **Variable expansion** - `${VARIABLE}` placeholders expanded at runtime
- **Tool-specific behavior** - each tool gets a temporary, expanded config

## 🔄 Complete Setup Workflow

```bash
cd my-project
ai init                                    # Set up project structure and workflow templates
ai claude                                 # Launch Claude Code (default profile)
ai claude --profile memory              # Launch Claude Code (with memory servers)  
ai cursor --profile devops              # Launch Cursor (with GitLab write access)
```

### Profile Examples

```bash
# Development workflow
ai claude --profile persistent           # Enhanced AI with memory
ai cursor-app --profile default         # Basic development (GUI)

# Repository operations  
ai claude --profile devops              # GitLab write + Kubernetes
ai cursor --profile qa                  # Testing tools + GitLab read-only (CLI)

# Research and exploration
ai claude --profile research            # Search and navigation tools
```

### Sub Agent Usage Examples

```bash
# After launching Claude Code with appropriate profile
ai claude --profile devops

# In Claude Code, agents are automatically available:
# "Deploy this branch to staging" → auto-delegates to devops-deployer
# "Review this pull request" → auto-delegates to core-dev-reviewer  
# "Run tests for the auth module" → auto-delegates to qa-test-runner
# "Research GraphQL best practices" → auto-delegates to research-synthesizer

# Or invoke explicitly:
# /agents devops-deployer "Deploy to production"
# /agents qa-test-runner "Analyze test coverage"
```

## 🎨 Integration Examples

### Use in any project
```bash
cd my-app
ai init
ai claude                  # Launch Claude Code
# Ask: "Show me GitLab issues for this project"
```
## 🛠 Development Workflow

### Daily Usage
```bash
# Morning setup - lightweight profile
cd project-directory  
ai cursor-app                            # Start with default profile (GUI)

# Long-term project work - remembers context
ai claude --profile persistent          # Remembers previous conversations

# Repository operations
ai cursor --profile devops               # GitLab operations + Kubernetes (CLI)
```

### Multiple Projects
```bash
# All projects share the same global profiles and environment
cd project-a && ai init && ai cursor-app --profile default
cd ../project-b && ai init && ai claude --profile persistent
cd ../project-c && ai cursor --profile qa    # Quality assurance work (CLI)
```

## 🤝 Contributing

Interested in extending the AI development environment? See [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- **Adding new MCP servers** (third-party integrations)
- **Creating custom MCP servers** in the `mcp-servers/` directory
- **Adding new AI tools** and environment variables
- **Testing procedures** and contribution workflow
- **Code style guidelines** and examples

## 🚨 Troubleshooting

### Command not found: ai
```bash
# Check PATH
echo $PATH | grep "$HOME/.local/ai-dev/bin"

# If missing, add to shell profile
echo 'export PATH="$HOME/.local/ai-dev/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Environment variables not loading
```bash
# Check .env file exists and has correct format
cat .env

# Test loading
ai load
env | grep -E "(GITLAB|ATLASSIAN)"
```

### AI tools not recognizing APIs
```bash
# Check environment setup
ai check

# Verify MCP configuration
cat ~/.local/ai-dev/mcp.json

# Test with minimal environment
ai claude --help
```

### MCP servers not working
```bash
# Check if MCP servers are running
ps aux | grep -i mcp | grep -v grep

# Verify MCP configuration was processed correctly
cat mcp.json | grep -E "(GITLAB|ATLASSIAN)"

# Restart MCP servers
pkill -f "mcp-server" && ai init

# Check for variable substitution issues
ai load && ai init
```
