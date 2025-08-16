# AI Developer Project Architecture

```mermaid
graph TD
    %% User Actions
    U1[User runs install.sh] --> I1{Installation Mode}
    
    %% Installation Modes
    I1 -->|Local Files| L1[Local Installation]
    I1 -->|Remote| R1[Remote Clone from GitLab]
    
    %% Installation Process
    L1 --> SETUP[Setup Process]
    R1 --> SETUP
    
    SETUP --> S1[Create ~/.local/ai-dev/]
    S1 --> S2[Copy bin/ai to ~/.local/ai-dev/bin/]
    S2 --> S3[Copy MCP base layers and profiles from templates/]
    S3 --> S4[Generate ~/.local/ai-dev/.env from template with substitution]
    S4 --> S5[Add ~/.local/ai-dev/bin to PATH]
    
    %% Global Configuration
    S5 --> GC[Global Configuration Created]
    GC --> GC1["~/.local/ai-dev/.env<br/>🔧 Global environment variables"]
    GC --> GC2["~/.local/ai-dev/mcp-profiles/<br/>🔌 DRY profile architecture with base layers"]
    GC --> GC3["~/.local/ai-dev/bin/ai<br/>⚡ Main CLI command"]
    
    %% Project Usage
    U2[User: cd my-project] --> U3[User: ai init]
    
    %% AI Init Process
    U3 --> AI1[Load Global Environment]
    AI1 --> AI2["Process MCP Templates<br/>with Variable Substitution"]
    AI2 --> AI3[Create Project-Specific Configs]
    
    %% Project Files Created
    AI3 --> PC1[".claude/.mcp.json → ~/.local/ai-dev/mcp.json<br/>📱 Claude Code MCP config (symlink)"]
    AI3 --> PC2[".cursor/mcp.json → ~/.local/ai-dev/mcp.json<br/>🎯 Cursor MCP config (symlink)"]
    AI3 --> PC3[".cursor/rules.json<br/>📋 Auto-configured for CLAUDE.md"]
    AI3 --> PC4[".claude/engineering-workflow.md<br/>🛠️ Complete engineering workflow"]
    AI3 --> PC5["CLAUDE.local.md<br/>📝 Local workflow reference"]
    AI3 --> PC6[".claude/agents/<br/>🤖 4 specialized sub agents"]
    
    %% Tool Launch
    U4[User: ai claude] --> TL1[Load Environment]
    U5[User: ai cursor] --> TL1
    U6[User: ai claude-app] --> TL1
    U7[User: ai cursor-app] --> TL1
    
    TL1 --> TL2[Global: ~/.local/ai-dev/.env]
    TL1 --> TL3[Local: project/.env]
    TL2 --> TL4[Merged Environment]
    TL3 --> TL4
    TL4 --> TL5["Launch Tool with<br/>Full MCP Stack"]
    
    %% MCP Servers
    TL5 --> MCP[MCP Servers Running]
    MCP --> M1[📊 GitLab API]
    MCP --> M2[🏗️ Atlassian JIRA/Confluence]
    MCP --> M3[📁 File System]
    MCP --> M4[🔍 Git Operations]
    MCP --> M5[💾 Memory Bank]
    MCP --> M6[🔍 DuckDuckGo Search]
    MCP --> M7[🧠 Sequential Thinking]  
    MCP --> M8[⚙️ Kubernetes]
    MCP --> M9[🧪 Testing Tools]
    
    %% Styling
    classDef userAction fill:#e1f5fe
    classDef globalConfig fill:#f3e5f5
    classDef projectConfig fill:#e8f5e8
    classDef mcpServer fill:#fff3e0
    
    class U1,U2,U3,U4,U5,U6,U7 userAction
    class GC1,GC2,GC3 globalConfig
    class PC1,PC2,PC3,PC4,PC5,PC6 projectConfig
    class M1,M2,M3,M4,M5,M6,M7,M8,M9 mcpServer
```

## How It Works

### 1. One-Time AI Development Setup
```bash
# Install the AI development environment
./install.sh

# Configure your personal AI credentials
ai setup
```

**Creates global configuration in `~/.local/ai-dev/`:**
- 🔧 **Global environment** (`~/.local/ai-dev/.env`) - Your AI development credentials  
- 🔌 **MCP profiles** (`~/.local/ai-dev/mcp-profiles/`) - DRY profile architecture with base layers
- 📚 **MCP base layers** (`~/.local/ai-dev/mcp-layers/`) - Reusable base layer components
- ⚡ **CLI command** (`~/.local/ai-dev/bin/ai`) - Main launcher with CLI/app separation

**The `ai setup` command:**
- Shows you exactly where to find your credentials file
- Lists which variables need your actual values
- Optionally opens the file in your editor
- Provides clear instructions on what credentials to add

### 2. Per-Project Setup
```bash
cd my-project
ai init  # Creates project-specific configs
```

**Creates project-specific configurations:**
- 📱 **Claude Code config** (`.claude/.mcp.json` → `~/.local/ai-dev/mcp.json`) - Symlinked MCP config
- 🎯 **Cursor config** (`.cursor/mcp.json` → `~/.local/ai-dev/mcp.json`) - Symlinked MCP config  
- 📋 **Engineering workflow** (`.claude/engineering-workflow.md`) - Complete JIRA integration workflow
- 📝 **Local workflow reference** (`CLAUDE.local.md`) - Not committed to version control
- 🤖 **Claude Sub Agents** (`.claude/agents/`) - 4 specialized workflow assistants
- 📋 **Cursor rules** (`.cursor/rules.json`) - Auto-configured for project instructions

### 3. Launch AI Tools
```bash
ai claude      # Launch Claude Code (desktop app)
ai claude-app  # Launch Claude Desktop app
ai cursor      # Launch Cursor CLI (cursor-agent)
ai cursor-app  # Launch Cursor app (full editor)
```

**Environment loading order:**
1. 🌐 **Global AI credentials** from `~/.local/ai-dev/.env` (GitLab, Datadog, Atlassian, etc.)
2. 🏠 **Project-specific overrides** from project `.env` (database URLs, API secrets, etc.)
3. 🚀 **Launch tool** with full MCP server stack

**Note:** Most projects won't need a `.env` file - your AI tools use the global credentials. Only create project `.env` files for project-specific overrides.

### 4. MCP Servers Available (Profile-Based)
- 📊 **GitLab** - Issues, MRs, repositories (read-only for qa, read-write for devops)
- 🏗️ **Atlassian** - JIRA tickets, Confluence pages (all profiles)
- 📁 **File System** - File operations and project structure (all profiles)
- 🔍 **Git** - Repository operations and history (all profiles)
- 💾 **Memory Bank** - Persistent knowledge storage (persistent, research profiles)
- 🔍 **DuckDuckGo** - Real-time web search (research profile)
- 🧠 **Sequential Thinking** - Step-by-step reasoning (research profile)
- ⚙️ **Kubernetes** - Cluster operations (devops profile)
- 🧪 **Testing Tools** - Cypress, test analyzers (qa profile)

## Key Benefits

✅ **One installation, all projects** - Global MCP profiles work everywhere  
✅ **Centralized credentials** - Set once, use everywhere with smart sync (`ai env-sync`)
✅ **5 specialized profiles** - Default, persistent, devops, qa, research profiles available
✅ **Symlinked configurations** - Projects reference global configs (no duplication)
✅ **Cross-tool compatibility** - Same MCP servers work in Claude Code, Cursor, etc.  
✅ **Engineering workflows** - Built-in JIRA integration and 4 specialized sub agents
✅ **Smart environment management** - Global `.env` with local project overrides

## Understanding Environment Variables

### AI Development Credentials (Global)
**Location:** `~/.local/ai-dev/.env`  
**Contains:** Personal API keys and tokens for AI development
```bash
GITLAB_PERSONAL_ACCESS_TOKEN=your-gitlab-token
GITLAB_API_URL=https://gitlab.example.com
GIT_AUTHOR_NAME="Your Name"
GIT_AUTHOR_EMAIL="your-email@company.com"
```

### Project-Specific Variables (Optional)
**Location:** `your-project/.env`  
**Contains:** Project's runtime configuration
```bash
DATABASE_URL=postgres://localhost/myapp
REDIS_URL=redis://localhost:6379
API_SECRET=project-specific-secret
```

**Key Point:** These are separate concerns. AI tools need your personal API credentials, while your application needs project-specific configuration.

## Profile System

### Available Profiles
- **`default`** - Basic MCP server setup
- **`devops`** - DevOps-focused with GitLab and Kubernetes
- **`qa`** - QA-focused with testing and validation tools
- **`research`** - Research-focused with memory and search capabilities
- **`persistent`** - Memory-enabled for long-term project knowledge

### Profile Selection
```bash
ai claude --profile devops      # Claude Code with devops profile
ai claude-app --profile qa     # Claude Desktop with qa profile
ai cursor --profile research   # Cursor CLI with research profile
ai cursor-app --profile devops # Cursor app with devops profile
```

### Profile Architecture (DRY Base Layers)
**Base Layers:**
- **common**: Core tools (filesystem, git) - included in all profiles
- **conversational**: Serena conversational AI - included in most profiles  
- **persistent**: Memory-bank for cross-session persistence

**Profile Composition:**
- **default**: layers=[common] + atlassian
- **persistent**: layers=[common, conversational, persistent]
- **devops**: layers=[common, conversational] + gitlab(RW) + k8s
- **qa**: layers=[common, conversational] + gitlab(RO) + cypress + test-analyzer
- **research**: layers=[common, conversational, persistent] + search tools