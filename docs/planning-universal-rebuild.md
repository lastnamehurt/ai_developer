# Planning: Universal AI Developer Tool

## Project Vision

Create a universal, cross-platform CLI tool for managing AI development environments that:
- Works for any developer on any machine (personal or professional)
- Supports multiple AI tools (Cursor, Claude Code, Zed, etc.)
- Provides profile-based MCP server configurations
- Makes onboarding to new machines/projects trivial
- Remains extensible and community-friendly

## Key Improvements Over Original

### 1. Universal (Not Company-Specific)
- **Replace**: GitLab → Generic Git provider support (GitHub, GitLab, Bitbucket)
- **Replace**: Company-specific JIRA → Generic issue tracker support
- **Add**: Plugin system for company-specific extensions
- **Remove**: Hard-coded company URLs and conventions

### 2. Enhanced Profile System
- User-defined custom profiles (not just built-in ones)
- Profile inheritance (extend base profiles)
- Profile templates for common scenarios
- Easy profile sharing (export/import)

### 3. Better Tool Support
- **Keep**: Cursor, Claude Code/Desktop
- **Add**: Zed, VS Code with AI extensions, any tool that supports MCP
- **Add**: Auto-detection of installed AI tools
- **Add**: Tool-agnostic configuration where possible

### 4. Improved Installation & Distribution
- **Option 1**: Homebrew/package manager support
- **Option 2**: Single binary distribution (Go/Rust)
- **Option 3**: NPM package (if staying with Node/shell)
- **Keep**: Direct git clone as fallback
- **Add**: Version management (update notifications)

### 5. Plugin/Extension Architecture
- MCP server registry (discover community servers)
- Easy custom MCP server integration
- Plugin hooks for custom commands
- Profile marketplace/sharing

### 6. Cross-Platform Excellence
- Fully test on macOS, Linux, and Windows (WSL)
- Shell-agnostic (bash, zsh, fish, etc.)
- Path handling for all platforms
- Better error messages for platform-specific issues

## Core Features to Preserve

### From Original ✅
- **Profile-based MCP configurations**: Different tool sets for different contexts
- **Environment variable management**: Single source of truth for API keys
- **Project initialization**: Quick setup for new projects
- **Tool launching with context**: Automatic config injection
- **Memory/persistence**: Cross-session context preservation
- **Testing framework**: Comprehensive test coverage

### New Features to Add 🆕
- **MCP server discovery**: Browse and install community servers
- **Profile templates**: Quick-start profiles for common scenarios
- **Better docs**: Auto-generated from code/configs
- **Health checks**: Verify MCP server connectivity
- **Backup/restore**: Easy migration between machines
- **Dry-run mode**: Preview changes before applying

## Architecture Decisions

### Technology Stack
**Option A: Shell (bash/zsh) + Python**
- ✅ Pros: Easy to modify, portable, no compilation
- ❌ Cons: Dependency management, slower execution
- **Use case**: Rapid prototyping, maximum portability

**Option B: Go**
- ✅ Pros: Single binary, fast, excellent CLI libraries (cobra, viper)
- ❌ Cons: Longer dev time, compilation required
- **Use case**: Production-ready, distribution-focused

**Option C: Rust**
- ✅ Pros: Performance, safety, great CLI ecosystem (clap)
- ❌ Cons: Steeper learning curve, longer compile times
- **Use case**: Maximum performance and safety

**Recommendation**: Start with **Shell + Python** for speed, migrate to **Go** if distribution becomes important.

### Directory Structure
```
~/.aidev/                          # New shorter name
├── config/
│   ├── profiles/                  # Profile definitions
│   │   ├── default.json
│   │   ├── devops.json
│   │   └── custom/                # User-defined profiles
│   ├── mcp-servers/               # MCP server configs
│   │   ├── filesystem.json
│   │   ├── git.json
│   │   └── custom/                # User-installed servers
│   └── tools.json                 # Installed AI tool paths
├── .env                           # Global environment variables
├── memory-banks/                  # Persistent memory storage
├── plugins/                       # User plugins/extensions
├── cache/                         # Cached data
└── logs/                          # Operation logs

# Per-project
.aidev/
├── config.json                    # Project-specific overrides
├── .env                           # Project environment variables
└── profile                        # Active profile name
```

### CLI Command Structure
```bash
# Setup & Installation
aidev install                      # Install/update the tool
aidev setup                        # Interactive setup wizard
aidev doctor                       # Health check everything

# Project Management
aidev init [profile]               # Initialize project
aidev config [set|get|list]        # Manage configuration
aidev env [set|get|list|sync]      # Manage environment variables

# Tool Launching
aidev cursor [--profile <name>]    # Launch Cursor
aidev claude [--profile <name>]    # Launch Claude Code
aidev zed [--profile <name>]       # Launch Zed
aidev tool <name> [--profile]      # Launch any registered tool

# Profile Management
aidev profile list                 # List all profiles
aidev profile show <name>          # Show profile details
aidev profile create <name>        # Create new profile
aidev profile edit <name>          # Edit profile
aidev profile export <name>        # Export to share
aidev profile import <file>        # Import from file

# MCP Server Management
aidev mcp list                     # List installed servers
aidev mcp search <query>           # Search registry
aidev mcp install <name>           # Install server
aidev mcp remove <name>            # Remove server
aidev mcp test <name>              # Test server connectivity

# Backup & Migration
aidev backup [path]                # Backup configuration
aidev restore <path>               # Restore from backup
aidev export                       # Export for sharing
aidev import <path>                # Import configuration
```

## Profile System Design

### Profile Schema
```json
{
  "name": "devops",
  "description": "Infrastructure and deployment workflows",
  "extends": "default",                    // Optional: inherit from another profile
  "mcp_servers": [
    {
      "name": "filesystem",
      "enabled": true
    },
    {
      "name": "git",
      "enabled": true,
      "config": {
        "provider": "github"               // Profile-specific overrides
      }
    },
    {
      "name": "kubernetes",
      "enabled": true
    }
  ],
  "environment": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",     // Variable expansion
    "KUBECONFIG": "${HOME}/.kube/config"
  },
  "tools": {
    "cursor": {
      "enabled": true,
      "settings": {}                       // Tool-specific settings
    }
  }
}
```

### Built-in Profiles

1. **default**: General development (filesystem, git, basic tools)
2. **minimal**: Bare minimum (filesystem only)
3. **researcher**: Investigation (web search, documentation, memory)
4. **fullstack**: Web development (filesystem, git, postgres, redis)
5. **devops**: Infrastructure (kubernetes, docker, cloud providers)
6. **data**: Data science (jupyter, databases, visualization)

## MCP Server Registry

### Registry Schema
```json
{
  "name": "kubernetes",
  "description": "Kubernetes cluster management",
  "author": "community",
  "repository": "https://github.com/user/mcp-kubernetes",
  "version": "1.0.0",
  "install": {
    "type": "npm",                         // or "docker", "binary", "script"
    "command": "npm install -g @ai/mcp-kubernetes"
  },
  "configuration": {
    "required": ["KUBECONFIG"],
    "optional": ["K8S_NAMESPACE"]
  },
  "tags": ["devops", "kubernetes", "infrastructure"]
}
```

## Implementation Phases

### Phase 1: Core Foundation (MVP)
- [ ] Basic CLI structure with subcommands
- [ ] Configuration file management (profiles, mcp servers)
- [ ] Environment variable handling
- [ ] Tool launcher (Cursor, Claude Code)
- [ ] Profile system (built-in profiles only)
- [ ] Installation script

### Phase 2: Enhanced Functionality
- [ ] Custom profile creation/editing
- [ ] MCP server testing and health checks
- [ ] Better error handling and diagnostics
- [ ] Auto-update mechanism
- [ ] Backup/restore functionality

### Phase 3: Community Features
- [ ] MCP server registry integration
- [ ] Profile import/export
- [ ] Plugin system
- [ ] Documentation generator
- [ ] Telemetry (opt-in)

### Phase 4: Polish & Distribution
- [ ] Cross-platform testing
- [ ] Package manager distribution
- [ ] Interactive TUI for setup
- [ ] Comprehensive documentation
- [ ] Example configurations and tutorials

## Success Metrics

1. **Installation Time**: < 2 minutes from clone to first launch
2. **Onboarding Time**: < 5 minutes to configure and launch AI tool
3. **Cross-Platform**: Works on macOS, Linux, Windows (WSL)
4. **Documentation**: Every command has `--help` and examples
5. **Testing**: >80% code coverage
6. **Community**: Easy to add custom MCP servers without forking

## Open Questions

1. **Name**: `aidev`, `ai-dev`, `aikit`, `devai`, something else?
2. **Language**: Start with shell/Python or go straight to Go?
3. **MCP Registry**: Self-hosted or use GitHub as registry?
4. **Distribution**: Homebrew first or GitHub releases?
5. **License**: MIT, Apache 2.0, or other?
6. **Multi-user**: Support team-shared profiles?

## Next Steps

1. Decide on name and basic architecture
2. Create initial project structure
3. Implement Phase 1 MVP
4. Test on multiple platforms
5. Document and iterate
