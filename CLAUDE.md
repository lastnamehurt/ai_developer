# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Testing
- `./tests/run-tests.sh` - Run all test suites with comprehensive reporting
- `./tests/run-tests.sh -v` - Run tests with verbose output
- `./tests/run-tests.sh -f` - Run tests with fail-fast (stop on first failure)
- `./tests/run-tests.sh utils` - Run only tests matching pattern (e.g., "utils", "core", "integration")
- `./tests/test-ai-utils.sh` - Run utility function tests only
- `./tests/test-ai-core.sh` - Run core function tests only
- `./tests/test-ai-project.sh` - Run project initialization tests only
- `./tests/test-ai-integration.sh` - Run integration tests only

### Installation and Updates
- `./install.sh` - Install/update the AI development environment from local files
- `ai install` - Update from GitHub repository (if already installed)

### Development Commands
- `ai init` - Initialize project with AI tool configurations
- `ai check` - Verify environment setup and configuration
- `ai setup` - Configure AI development credentials
- `ai sync` - Sync Claude configs to Cursor format
- `ai env-sync` - Sync local .env variables to global AI environment

### AI Tool Launching
- `ai claude` - Launch Claude Code with default profile
- `ai claude --profile <name>` - Launch Claude Code with specific profile (default, core-dev, repo-ops, qa, research)
- `ai cursor` - Launch Cursor with default profile
- `ai cursor --profile <name>` - Launch Cursor with specific profile

## Architecture

### Core Components

#### Modular Shell Architecture
The project uses a modular shell script architecture split across four main components:

- **`bin/ai`** - Main entry point and command router, handles profile-aware tool launching
- **`bin/ai-utils.sh`** - Utility functions for logging, file operations, and environment handling
- **`bin/ai-core.sh`** - Core environment loading and profile management functions
- **`bin/ai-project.sh`** - Project initialization, workflow management, and configuration setup

#### Profile-Based MCP Configuration
The system implements a sophisticated profile system with 5 pre-configured profiles using a DRY base layer approach:

**Base Layers:**
- **base.common.json**: Core tools (filesystem, git) - included in all profiles
- **base.conversational.json**: Serena conversational AI - included in most profiles
- **base.persistent.json**: Memory-bank for cross-session persistence

**Profile Matrix:**
| Server | default | persistent | devops | qa | research |
|--------|---------|--------|--------|----|----------|
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

Profiles are stored in `~/.local/ai-dev/mcp-profiles/` and merged with base layers at runtime with environment variable substitution.

#### Claude Sub Agent Integration

The system includes **Claude Sub Agents** as specialized workflow assistants that work on top of the MCP profile system:

**Architecture:**
- **Profiles** = Define which MCP servers/tools exist (your "toolbelt" and environment)
- **Sub Agents** = Purpose-built specialists with their own context windows and prompts

**Agent Locations:**
- **Project scope**: `.claude/agents/` (takes precedence, version controlled)
- **User scope**: `~/.claude/agents/` (personal agents)

**Built-in Agents:**
- **devops-deployer**: Kubernetes and GitLab deployment specialist
- **qa-test-runner**: E2E/API test execution and coverage analysis
- **core-dev-reviewer**: Code review with security and performance focus
- **research-synthesizer**: External research and documentation synthesis

**Tool Access:**
- Agents inherit all MCP tools from the active profile by default
- Can be restricted via `/agents` UI if needed
- Integrates with memory-bank for persistent state across sessions

#### Memory Persistence Strategy

**Primary Backend: memory-bank**
- Cross-session persistence using `MEMORY_BANK_ROOT` storage
- Available in `persistent` and `research` profiles  
- Stored in `~/.local/ai-dev/memory-banks` by default

**Context Preservation:**
- Memory persists across different profile sessions when using same `MEMORY_BANK_ROOT`
- Base layers ensure consistent memory configuration
- Long-term project continuity through persistent storage

#### Centralized Environment Management
- **Global Environment**: `~/.local/ai-dev/.env` - Shared credentials across all projects
- **Local Override**: Project-specific `.env` files can override global variables
- **Variable Substitution**: MCP configs use `${VAR}` placeholders for dynamic credential injection
- **Loading Order**: Global variables loaded first, then local variables override them

### Installation System

#### Multi-Mode Installation
The `install.sh` script supports two installation modes:

1. **Local Installation**: When run from cloned repository directory
2. **Remote Installation**: Downloads from GitHub repository automatically

#### File Structure Management
- **Global Directory**: `~/.local/ai-dev/` contains all shared configurations
- **Symlinked Configs**: Project configs are symlinked to global profiles
- **Template Processing**: Uses `envsubst` or `sed` fallback for variable substitution
- **Dependency Installation**: Automatically installs required MCP servers and tools

### Sub Agent & Profile Integration

**Workflow Examples:**
- `ai claude --profile devops` + **devops-deployer** = Full K8s + GitLab deployment capabilities
- `ai claude --profile qa` + **qa-test-runner** = Complete testing workflow with overlap analysis
- `ai claude --profile persistent` + **core-dev-reviewer** = Code review with memory of past decisions
- `ai claude --profile research` + **research-synthesizer** = Research with persistent knowledge storage

**Agent Management:**
- Agents created by `ai init` are project-specific and version controlled
- Use `/agents` command in Claude Code to create, edit, or manage agents
- Agents automatically delegate tasks and preserve main conversation context

### Engineering Workflow Integration

The system includes built-in engineering workflow templates that provide:

- **JIRA Integration**: Automated ticket creation, status updates, and linking
- **Git Workflow**: Standardized branch naming (`JIRA-###-description`) and commit patterns
- **Documentation Standards**: Consistent project documentation approach
- **Testing Guidelines**: Quality assurance workflow integration

Workflow files are automatically integrated when running `ai init` on projects.

### Test Framework

#### Comprehensive Test Suite
- **Modular Tests**: Separate test files for each component (`test-ai-utils.sh`, `test-ai-core.sh`, etc.)
- **Test Runner**: `run-tests.sh` provides unified test execution with filtering, verbose output, and coverage analysis
- **Environment Validation**: Tests verify proper file structure, permissions, and dependency availability
- **Result Aggregation**: Comprehensive reporting with pass/fail statistics and detailed failure information

#### Test Categories
- **Unit Tests**: Individual function testing for utilities and core functions
- **Integration Tests**: End-to-end workflow testing
- **Environment Tests**: Configuration and setup validation

### Key Design Patterns

#### Function Organization
- **Utility Functions**: Pure functions for logging, file operations, path resolution
- **Core Functions**: Environment loading, profile resolution, tool launching
- **Project Functions**: Initialization workflows, template processing, configuration management

#### Error Handling
- **Graceful Degradation**: Falls back to alternative methods when preferred tools aren't available
- **Comprehensive Logging**: Structured logging with info, success, warning, and error levels
- **Validation**: Extensive input validation and environment checking

#### Configuration Management
- **Template-Based**: Distributable templates with placeholder substitution
- **Environment-Aware**: Automatic detection of available tools and credentials
- **Profile-Driven**: Different tool configurations for different use cases

### MCP Server Integration

#### Custom MCP Servers
- **Test Overlap Analyzer**: TypeScript-based MCP server for analyzing E2E test overlap (`mcp-servers/retire-e2e-tests/`)
- **K8s Server**: Go-based Kubernetes operations server installed via `go install`
- **Third-Party Servers**: GitLab, Atlassian, filesystem, git, and various other integrations

#### Server Management
- **Profile-Based Loading**: Different servers loaded based on profile selection
- **Environment Variable Injection**: Credentials automatically injected from environment
- **Fallback Mechanisms**: Alternative installation methods when primary approaches fail

## Usage Examples

### Basic Workflow Examples

#### Single Developer Workflow
```bash
# 1. Start development session with memory
ai claude --profile persistent

# 2. Start concurrent testing session  
ai claude --profile qa &

# 3. Use Cursor for UI development
ai cursor --profile default
```

#### Team Development Workflow
```bash
# DevOps Engineer
ai claude --profile devops
# Then use: /agents -> devops-deployer

# QA Engineer  
ai claude --profile qa
# Then use: /agents -> qa-test-runner

# Senior Developer (Code Review)
ai claude --profile persistent
# Then use: /agents -> core-dev-reviewer
```

### Profile Usage Patterns

#### Development Phases
```bash
# Research & Planning Phase
ai claude --profile research      # Web search, memory, research tools
# Use: /agents -> research-synthesizer

# Implementation Phase  
ai claude --profile persistent    # Code development with memory
ai cursor --profile default       # Alternative UI development

# Testing Phase
ai claude --profile qa           # Testing tools, GitLab read-only
# Use: /agents -> qa-test-runner

# Deployment Phase
ai claude --profile devops       # K8s, GitLab write access
# Use: /agents -> devops-deployer
```

#### Multi-Tool Concurrent Usage
```bash
# Terminal 1: Primary development with memory
ai claude --profile persistent

# Terminal 2: Deployment monitoring  
ai claude --profile devops

# Terminal 3: Test execution
ai claude --profile qa

# Terminal 4: UI/Visual development
ai cursor --profile default
```

### Sub Agent Combinations

#### DevOps Workflow
```bash
ai claude --profile devops
# In Claude: /agents -> devops-deployer
# Capabilities: K8s deployments, GitLab pipelines, infrastructure
```

#### QA Workflow  
```bash
ai claude --profile qa
# In Claude: /agents -> qa-test-runner  
# Capabilities: E2E tests, API tests, coverage analysis
```

#### Code Review Workflow
```bash
ai claude --profile persistent
# In Claude: /agents -> core-dev-reviewer
# Capabilities: Security review, performance analysis, persistent memory
```

#### Research Workflow
```bash
ai claude --profile research
# In Claude: /agents -> research-synthesizer
# Capabilities: Web search, documentation synthesis, persistent knowledge
```

### Advanced Use Cases

#### Full Engineering Pipeline
```bash
# 1. Research & Requirements
ai claude --profile research
# Use research-synthesizer for external docs, specifications

# 2. Development & Code Review
ai claude --profile persistent  
# Use core-dev-reviewer for security/performance review

# 3. Testing & Validation
ai claude --profile qa
# Use qa-test-runner for comprehensive testing

# 4. Deployment & Operations
ai claude --profile devops
# Use devops-deployer for K8s and GitLab operations
```

#### Cross-Profile Data Flow
```bash
# Research findings persist across profiles when using memory-bank
ai claude --profile research    # Research phase with memory
ai claude --profile persistent  # Development phase retains research context
ai claude --profile devops      # Deployment phase (no memory by default)
```

### Project-Specific Examples

#### Large Scale Web Application
```bash
# Frontend Development
ai cursor --profile default      # UI components, styling

# Backend Development  
ai claude --profile persistent   # API development with memory

# Infrastructure & Deployment
ai claude --profile devops       # K8s configs, GitLab CI/CD

# Quality Assurance
ai claude --profile qa           # E2E tests, API testing
```

#### Data Science Project
```bash
# Research & Data Exploration
ai claude --profile research     # Literature review, methodology

# Development & Experimentation
ai claude --profile persistent   # Model development with memory

# Testing & Validation
ai claude --profile qa           # Test data pipelines, validation
```

### Troubleshooting & Tips

#### Profile Selection Guidelines
- **default**: Lightweight, basic file operations
- **persistent**: Long-term development projects requiring memory
- **devops**: Infrastructure, deployment, CI/CD workflows  
- **qa**: Testing, validation, quality assurance
- **research**: External research, documentation, planning

#### Memory Management
- Use `persistent` or `research` profiles for memory across sessions
- Memory stored in `~/.local/ai-dev/memory-banks` by default
- Same memory bank shared across profiles when using same `MEMORY_BANK_ROOT`

#### Concurrent Usage Best Practices
- Use different profiles for different concerns (separation of duties)
- Background profiles with `&` for monitoring/secondary tasks
- Cursor for visual/UI work, Claude for logic/infrastructure
- Sub agents for specialized workflows within each profile