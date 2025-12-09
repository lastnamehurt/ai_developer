# aidev System Overview

A comprehensive visual guide to understanding how aidev works and how its powerful features connect together.

> **Note**: The diagrams below use Mermaid syntax, which renders automatically on GitHub, GitLab, and most modern markdown viewers. If you're viewing this in a plain text editor, you can preview the diagrams using VS Code with a Mermaid extension or online at [mermaid.live](https://mermaid.live).

## 🎯 High-Level Architecture

```mermaid
graph TB
    subgraph "User Entry Points"
        CLI[`ai` CLI Commands]
        TUI[Interactive TUI]
    end

    subgraph "Core Managers"
        ConfigMgr[ConfigManager<br/>Directory Init<br/>Env Merging]
        ProfileMgr[ProfileManager<br/>Load/Save Profiles<br/>Inheritance]
        MCPMgr[MCPManager<br/>Registry Fetch<br/>Install/Test]
        ToolMgr[ToolManager<br/>Tool Detection<br/>Config Resolution]
        WorkflowEngine[WorkflowEngine<br/>Multi-step Orchestration]
    end

    subgraph "Configuration Layers"
        Global[Global Config<br/>~/.aidev/]
        Project[Project Config<br/>./.aidev/]
        ProfileDefs[Profile Definitions<br/>JSON Files]
    end

    subgraph "Data Processing"
        MCPGen[MCPConfigGenerator<br/>Tool-specific Configs]
        EnvMerge[Environment Merger<br/>Global + Project]
        Quickstart[QuickstartDetector<br/>Stack Detection]
    end

    subgraph "Output"
        ToolConfigs[Tool Config Files<br/>~/.claude.json<br/>~/.codex/config.toml]
        LaunchedTools[Launched AI Tools<br/>Claude, Cursor, Codex<br/>Gemini, Ollama]
    end

    CLI --> ConfigMgr
    CLI --> ProfileMgr
    CLI --> MCPMgr
    CLI --> ToolMgr
    CLI --> WorkflowEngine
    TUI --> ConfigMgr
    TUI --> ProfileMgr

    ConfigMgr --> Global
    ConfigMgr --> Project
    ProfileMgr --> ProfileDefs
    MCPMgr --> ProfileDefs

    ProfileMgr --> MCPGen
    ConfigMgr --> EnvMerge
    Quickstart --> ProfileMgr

    MCPGen --> ToolConfigs
    EnvMerge --> ToolConfigs
    ToolConfigs --> LaunchedTools
    ToolMgr --> LaunchedTools
```

## 🔄 Complete Tool Launch Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as ai CLI
    participant ConfigMgr as ConfigManager
    participant ProfileMgr as ProfileManager
    participant MCPMgr as MCPManager
    participant MCPGen as MCPConfigGenerator
    participant ToolMgr as ToolManager
    participant Tool as AI Tool

    User->>CLI: ai cursor --profile web
    CLI->>ConfigMgr: Ensure directories initialized
    ConfigMgr-->>CLI: ✓ Initialized
    
    CLI->>ProfileMgr: Load profile "web"
    ProfileMgr->>ProfileMgr: Check inheritance (extends)
    ProfileMgr->>ProfileMgr: Merge parent profile
    ProfileMgr-->>CLI: Profile object with MCP servers
    
    CLI->>ConfigMgr: Get merged environment
    ConfigMgr->>ConfigMgr: Merge global + project .env
    ConfigMgr-->>CLI: Complete env vars
    
    CLI->>MCPGen: Generate config for "cursor"
    MCPGen->>MCPMgr: Get server definitions
    MCPMgr-->>MCPGen: Server configs (git, github, etc.)
    MCPGen->>MCPGen: Expand ${ENV_VARS}
    MCPGen->>MCPGen: Write cursor-specific format
    MCPGen-->>CLI: Config written to ~/.cursor/mcp.json
    
    CLI->>ToolMgr: Launch cursor
    ToolMgr->>ToolMgr: Detect cursor binary
    ToolMgr->>ToolMgr: Resolve config path
    ToolMgr->>Tool: Execute cursor with env vars
    Tool-->>User: Cursor launched with MCP context
```

## 📊 Configuration Hierarchy

```mermaid
graph TD
    subgraph "Priority Order"
        P1[1. Command-line --profile flag]
        P2[2. Global Active Profile<br/>~/.aidev/.active-profile]
        P3[3. Project Profile<br/>./.aidev/profile]
        P4[4. Default Profile<br/>'default']
    end

    subgraph "Environment Variables"
        E1[Global Env<br/>~/.aidev/.env]
        E2[Project Env<br/>./.aidev/.env]
        E3[Merged Result<br/>Project overrides Global]
    end

    subgraph "Profile Sources"
        PS1[Built-in Profiles<br/>~/.aidev/config/profiles/]
        PS2[Custom Profiles<br/>~/.aidev/config/profiles/custom/]
        PS3[Profile Inheritance<br/>extends field]
    end

    P1 --> P2
    P2 --> P3
    P3 --> P4
    
    E1 --> E3
    E2 --> E3
    
    PS1 --> PS3
    PS2 --> PS3
```

## 🎭 Profile System Deep Dive

```mermaid
graph LR
    subgraph "Profile Definition"
        PD[Profile JSON<br/>name, description<br/>extends, tags]
        MS[MCP Servers<br/>git, github<br/>postgres, k8s]
        ENV[Environment<br/>GITHUB_TOKEN<br/>DB_URL]
        TOOLS[Tool Configs<br/>Cursor, Claude<br/>Codex, Gemini]
    end

    subgraph "Profile Types"
        BUILTIN[Built-in<br/>web, infra, qa]
        CUSTOM[Custom<br/>User-defined]
        INHERITED[Inherited<br/>extends parent]
    end

    subgraph "Profile Usage"
        QUICKSTART[Quickstart<br/>Auto-detection]
        MANUAL[Manual Selection<br/>ai use profile]
        FLAG[CLI Flag<br/>--profile name]
    end

    PD --> MS
    PD --> ENV
    PD --> TOOLS
    
    PD --> BUILTIN
    PD --> CUSTOM
    PD --> INHERITED
    
    BUILTIN --> QUICKSTART
    CUSTOM --> MANUAL
    INHERITED --> FLAG
```

## 🔌 MCP Server Management Flow

```mermaid
graph TB
    subgraph "Discovery"
        REGISTRY[MCP Registry<br/>Remote + Cache]
        SEARCH[Search & Browse<br/>ai mcp search]
        TUI_BROWSE[TUI Browser<br/>ai mcp browse]
    end

    subgraph "Installation"
        INSTALL[Install Server<br/>ai mcp install]
        SAVE[Save Config<br/>~/.aidev/config/mcp-servers/]
        ENABLE[Enable in Profile<br/>Add to profile.json]
    end

    subgraph "Configuration"
        LOAD[Load Definition]
        EXPAND[Expand Env Vars<br/>${GITHUB_TOKEN}]
        GENERATE[Generate Tool Config<br/>Cursor/Claude/Codex]
    end

    subgraph "Usage"
        TEST[Test Connectivity<br/>ai mcp test]
        LAUNCH[Launch Tool<br/>ai cursor/claude]
        INJECT[Inject MCP Context]
    end

    REGISTRY --> SEARCH
    REGISTRY --> TUI_BROWSE
    SEARCH --> INSTALL
    TUI_BROWSE --> INSTALL
    INSTALL --> SAVE
    INSTALL --> ENABLE
    ENABLE --> LOAD
    LOAD --> EXPAND
    EXPAND --> GENERATE
    GENERATE --> TEST
    GENERATE --> LAUNCH
    LAUNCH --> INJECT
```

## 🚀 Workflow Orchestration System

```mermaid
graph TB
    subgraph "Workflow Definition"
        YAML[workflows.yaml<br/>Step definitions]
        PROMPTS[Prompt Templates<br/>src/aidev/prompts/]
        STEPS[Workflow Steps<br/>Assistant, Prompt, Timeout]
    end

    subgraph "Execution"
        RUN[Run Workflow<br/>ai workflow name]
        MANIFEST[Generate Manifest<br/>.aidev/workflow-runs/]
        EXECUTE[Execute Steps<br/>Multi-assistant]
        RESUME[Resume Execution<br/>--from-step]
    end

    subgraph "Assistants"
        CLAUDE[Claude Code]
        CODEX[Codex CLI]
        GEMINI[Gemini]
        OLLAMA[Ollama]
    end

    YAML --> STEPS
    PROMPTS --> STEPS
    STEPS --> RUN
    RUN --> MANIFEST
    MANIFEST --> EXECUTE
    EXECUTE --> CLAUDE
    EXECUTE --> CODEX
    EXECUTE --> GEMINI
    EXECUTE --> OLLAMA
    EXECUTE --> RESUME
```

## 🎯 Quickstart Detection Flow

```mermaid
graph LR
    subgraph "Detection Signals"
        JS[JavaScript<br/>package.json<br/>tsconfig.json]
        PY[Python<br/>pyproject.toml<br/>requirements.txt]
        DOCKER[Docker<br/>Dockerfile<br/>docker-compose.yml]
        K8S[Kubernetes<br/>*.yaml<br/>helm charts]
    end

    subgraph "Scoring"
        SCORE[Confidence Scores<br/>Per tech stack]
        TAGS[Tag Matching<br/>web, infra, python]
    end

    subgraph "Recommendation"
        REC[Profile Recommendation<br/>Based on tags]
        INIT[Initialize Project<br/>Create .aidev/]
    end

    JS --> SCORE
    PY --> SCORE
    DOCKER --> SCORE
    K8S --> SCORE
    SCORE --> TAGS
    TAGS --> REC
    REC --> INIT
```

## 🔐 Environment Variable Management

```mermaid
graph TB
    subgraph "Storage"
        GLOBAL_ENV[Global .env<br/>~/.aidev/.env]
        PROJ_ENV[Project .env<br/>./.aidev/.env]
        ENCRYPTED[Encrypted Values<br/>ENC::...]
    end

    subgraph "Operations"
        SET[Set Variable<br/>ai env set KEY value]
        LIST[List Variables<br/>ai env list]
        VALIDATE[Validate<br/>ai env validate]
        UNLOCK[Unlock Encryption<br/>ai env unlock]
    end

    subgraph "Usage"
        MERGE[Merge Global + Project<br/>Project overrides]
        EXPAND[Expand ${VARS}<br/>In MCP configs]
        INJECT[Inject to Tools<br/>Environment]
    end

    SET --> GLOBAL_ENV
    SET --> PROJ_ENV
    SET --> ENCRYPTED
    LIST --> GLOBAL_ENV
    LIST --> PROJ_ENV
    VALIDATE --> MERGE
    UNLOCK --> ENCRYPTED
    MERGE --> EXPAND
    EXPAND --> INJECT
```

## 🛠️ Tool Integration Points

```mermaid
graph TB
    subgraph "Tool Detection"
        DETECT[Detect Binary<br/>On PATH]
        CONFIG_PATH[Resolve Config Path<br/>Tool-specific]
        VERSION[Check Version<br/>Optional]
    end

    subgraph "Config Generation"
        CURSOR[Cursor<br/>~/.cursor/mcp.json]
        CLAUDE[Claude Code<br/>~/.claude/mcp.json]
        CODEX[Codex<br/>~/.codex/config.toml]
        GEMINI[Gemini<br/>~/.gemini/settings.json]
        ZED[Zed<br/>~/.zed/mcp.json]
    end

    subgraph "Launch"
        ENV_INJECT[Inject Environment<br/>Merged vars]
        EXEC[Execute Binary<br/>With config]
        MCP_CONTEXT[MCP Context<br/>Available to tool]
    end

    DETECT --> CONFIG_PATH
    CONFIG_PATH --> CURSOR
    CONFIG_PATH --> CLAUDE
    CONFIG_PATH --> CODEX
    CONFIG_PATH --> GEMINI
    CONFIG_PATH --> ZED
    CURSOR --> ENV_INJECT
    CLAUDE --> ENV_INJECT
    CODEX --> ENV_INJECT
    GEMINI --> ENV_INJECT
    ZED --> ENV_INJECT
    ENV_INJECT --> EXEC
    EXEC --> MCP_CONTEXT
```

## 📁 File Structure Overview

```
~/.aidev/                          # Global Configuration
├── config/
│   ├── profiles/                  # Profile definitions
│   │   ├── web.json
│   │   ├── infra.json
│   │   └── custom/               # User-created profiles
│   └── mcp-servers/              # MCP server configs
│       ├── git.json
│       ├── github.json
│       └── custom/               # Custom servers
├── .env                          # Global environment variables
├── .active-profile               # Global active profile (legacy)
└── cache/
    └── mcp-registry.json         # Cached MCP registry

./.aidev/                         # Project Configuration
├── config.json                   # Project settings
├── profile                       # Active profile for project
├── .env                          # Project environment variables
├── workflows.yaml                # Workflow definitions
└── workflow-runs/                # Execution manifests
    └── workflow-name-timestamp.json

~/.cursor/mcp.json                # Generated tool configs
~/.claude/mcp.json
~/.codex/config.toml
~/.gemini/settings.json
~/.zed/mcp.json
```

## 🎯 Key Design Principles

1. **Single Source of Truth**: One profile definition → multiple tool configs
2. **Configuration Hierarchy**: Project overrides global, explicit overrides implicit
3. **Inheritance**: Profiles can extend others, reducing duplication
4. **Validation**: Preflight checks ensure everything works before launch
5. **Encryption**: Sensitive data is encrypted at rest
6. **Offline Support**: Cached registry and bundled fallbacks
7. **Tool Agnostic**: Same profile works across all supported tools

## 🔗 Feature Connections

- **Profiles** → Define MCP servers → **MCP Manager** → Generates configs → **Tool Launcher**
- **Quickstart** → Detects stack → Recommends **Profile** → Initializes **Project Config**
- **Workflows** → Uses **Profiles** → Launches **Tools** → Executes **MCP-enabled** assistants
- **Environment** → Merged into **MCP configs** → Injected into **Tools**
- **TUI** → Edits **Profiles** and **Environment** → Updates **Configs** → Reflects in **Tools**

## 🚀 Common User Journeys

### First-Time Setup
```
ai setup → Configure profiles → Set env vars → ai quickstart → ai cursor
```

### Daily Development
```
cd project → ai cursor (uses project profile) → Work with MCP context
```

### Profile Switching
```
ai use infra → ai cursor → Different MCP servers active
```

### Workflow Execution
```
ai workflow doc_improver README.md → Multi-step execution → Results
```

### MCP Server Addition
```
ai mcp search postgres → ai mcp install postgres → Enable in profile → ai cursor
```

---

**Next Steps:**
- [Architecture Details](architecture.md) - Deep dive into internals
- [Features Guide](features.md) - Complete feature reference
- [Commands Reference](commands.md) - All available commands