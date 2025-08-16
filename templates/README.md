# Templates Directory

This directory contains template files that are copied during project initialization (`ai init`) and system installation.

## Directory Structure

```
templates/
├── README.md                     # This file
├── mcp-profiles/                 # MCP profile configurations
│   ├── default.mcp.json         # Default profile (filesystem, git, atlassian)
│   ├── persistent.mcp.json      # Persistent profile (+ memory-bank, serena)
│   ├── devops.mcp.json          # DevOps profile (+ gitlab RW, k8s, serena)
│   ├── qa.mcp.json              # QA profile (+ gitlab RO, cypress, test-analyzer, serena)
│   └── research.mcp.json        # Research profile (+ duckduckgo, compass, sequentialthinking, memory-bank, serena)
├── mcp-layers/                   # Base layer configurations for DRY profile architecture
│   ├── base.common.json         # Core tools (filesystem, git) - included in all profiles
│   ├── base.conversational.json # Serena conversational AI - included in most profiles
│   └── base.persistent.json     # Memory-bank for cross-session persistence
├── agents/                       # Claude Sub Agent templates
│   ├── devops-deployer.md       # Kubernetes and GitLab deployment specialist
│   ├── qa-test-runner.md        # E2E/API test execution and coverage analysis
│   ├── core-dev-reviewer.md     # Security-focused code review agent
│   └── research-synthesizer.md  # External research and documentation synthesis
└── mcp.json                      # Legacy MCP server definitions (for reference)
```

## Profile System

The AI-Dev system uses a **DRY (Don't Repeat Yourself) profile architecture** with base layer inheritance:

### Base Layers

Base layers are shared JSON configurations that eliminate duplication across profiles:

- **`base.common.json`**: Core tools (filesystem, git) included in all profiles
- **`base.conversational.json`**: Serena conversational AI for enhanced interaction
- **`base.persistent.json`**: Memory-bank configuration for cross-session persistence

### Profile Resolution

When you select a profile (e.g., `ai claude --profile devops`), the system:

1. Loads the base layers specified in the profile's `"layers"` field
2. Merges them with the profile-specific `mcpServers` using `jq` (with Python fallback)
3. Performs environment variable substitution (`${VAR}` placeholders)
4. Creates a temporary merged configuration file

### Profile Matrix

| Server | default | persistent | devops | qa | research |
|--------|---------|------------|--------|----|----------|
| filesystem | ✓ | ✓ | ✓ | ✓ | ✓ |
| git | ✓ | ✓ | ✓ | ✓ | ✓ |
| atlassian | ✓ | – | – | – | – |
| serena | – | ✓ | ✓ | ✓ | ✓ |
| memory-bank | – | ✓ | – | – | ✓ |
| gitlab (RO) | – | – | – | ✓ | – |
| gitlab (RW) | – | – | ✓ | – | – |
| k8s | – | – | ✓ | – | – |
| cypress | – | – | – | ✓ | – |
| test-overlap-analyzer | – | – | – | ✓ | – |
| duckduckgo/compass/sequentialthinking | – | – | – | – | ✓ |

## Claude Sub Agents

Sub Agents are specialized workflow assistants that work on top of the MCP profile system:

### Agent Design

Each agent template includes:
- **YAML frontmatter** with `name` and `description` fields
- **Specialized prompts** for specific workflow tasks
- **Tool inheritance** from the active MCP profile
- **Best practices** for the specific domain

### Agent-Profile Alignment

| Agent | Best Profile | Primary Tools Used | Purpose |
|-------|--------------|-------------------|---------|
| **devops-deployer** | `devops` | gitlab, k8s, serena | Kubernetes deployments, GitLab pipeline management |
| **qa-test-runner** | `qa` | gitlab, cypress, test-overlap-analyzer, serena | Test execution and coverage analysis |
| **core-dev-reviewer** | `persistent` | filesystem, git, memory-bank, serena | Code review with memory of standards |
| **research-synthesizer** | `research` | duckduckgo, compass, sequentialthinking, memory-bank, serena | External research and documentation |

### Agent Usage

Sub Agents are automatically created in `.claude/agents/` when you run `ai init` in a project directory. Claude Code can:

- **Auto-delegate** tasks to appropriate agents based on context
- **Explicit invocation** via `/agents agent-name "task description"`
- **Inherit all MCP tools** from your active profile
- **Maintain separate context windows** to keep main conversation clean

## Environment Variables

Profiles support environment variable substitution using `${VAR}` or `${VAR:-default}` syntax:

```json
{
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
    "KUBECONFIG": "${KUBECONFIG:-${HOME}/.kube/config}"
  }
}
```

Common environment variables:
- `GITLAB_PERSONAL_ACCESS_TOKEN`: GitLab API access
- `GITLAB_API_URL`: GitLab instance URL
- `KUBECONFIG`: Kubernetes config file path
- `MEMORY_BANK_ROOT`: Memory persistence storage location

## Modifying Templates

### Adding New Profiles

1. Create `templates/mcp-profiles/new-profile.mcp.json`
2. Specify base layers in `"layers"` field: `["common", "conversational"]`
3. Add profile-specific servers in `"mcpServers"` section
4. Update documentation and profile matrix

### Adding New Base Layers

1. Create `templates/mcp-layers/base.new-layer.json`
2. Define common MCP servers for the layer
3. Include the layer in relevant profiles' `"layers"` arrays

### Adding New Sub Agents

1. Create `templates/agents/agent-name.md`
2. Include YAML frontmatter with `name` and `description`
3. Write specialized prompts for the workflow
4. Update this README with agent-profile alignment

### Testing Changes

Use the integrated test framework to validate template changes:

```bash
./tests/run-tests.sh profiles   # Test profile resolution
./tests/run-tests.sh agents     # Test agent creation
./tests/run-tests.sh -v         # Verbose testing
```