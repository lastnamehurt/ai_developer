# MCP Server Configuration Refactoring

## Summary

Refactored MCP server configurations from hardcoded Python dictionaries to external JSON files for easier management and updates.

## Changes Made

### Before ❌
```python
# src/aidev/mcp.py
def _get_builtin_servers(self) -> dict[str, dict]:
    return {
        "filesystem": {
            "name": "filesystem",
            "description": "...",
            "command": "npx",
            # ... 150+ lines of Python
        },
        # ... more servers
    }
```

**Problems**:
- Hard to add/modify servers (requires Python code changes)
- Not user-friendly for non-developers
- Changes require code review
- Difficult to version control individual servers

### After ✅
```
configs/mcp-servers/
├── filesystem.json
├── git.json
├── github.json
├── gitlab.json
└── ... (15 servers total)
```

```json
// configs/mcp-servers/filesystem.json
{
  "name": "filesystem",
  "description": "File system access and manipulation",
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"]
}
```

**Benefits**:
- ✅ Add servers without touching Python code
- ✅ Easy to read and edit JSON
- ✅ Each server is independently versioned
- ✅ Users can customize their local copies
- ✅ Simpler to review changes (one file per server)

## Real MCP Servers Added

All 15 servers from the user's production configuration:

### Core
- **filesystem** - File system access (@modelcontextprotocol)
- **git** - Git operations (git-mcp-server)

### Git Hosting
- **github** - GitHub API (@modelcontextprotocol)
- **gitlab** - GitLab API with CI/CD, wikis, milestones (@zereight)

### Testing
- **cypress** - End-to-end testing (local install)

### Project Management
- **atlassian** - JIRA + Confluence (remote MCP)

### Infrastructure
- **k8s** - Kubernetes cluster management (k8s-mcp-server)

### AI Tools
- **serena** - AI assistant (@oraios)
- **heimdall** - Monitoring (@shinzo-labs)
- **compass** - Code navigation (@liuyoshio)

### Memory & Context
- **memory-bank** - Persistent memory (@allpepper)
- **memory** - Official memory server (@modelcontextprotocol)
- **sequential-thinking** - Reasoning capabilities (@modelcontextprotocol)

### Research
- **duckduckgo** - Web search (Python/uvx)

### Database
- **postgres** - PostgreSQL access (@modelcontextprotocol)

## Code Changes

### 1. New Directory Structure
```
configs/
├── README.md                    # Documentation
└── mcp-servers/                 # MCP server configs
    ├── filesystem.json
    ├── git.json
    └── ... (15 total)
```

### 2. Updated `src/aidev/mcp.py`

**New method**: `_get_bundled_configs_dir()`
- Finds the configs directory
- Supports both development (`pip install -e .`) and production installs
- Works with PyInstaller bundling

**Updated method**: `init_builtin_servers()`
- Now copies JSON files from `configs/` to `~/.aidev/config/mcp-servers/`
- Only copies if file doesn't exist (preserves user customizations)

**Updated method**: `_get_builtin_servers()`
- Loads from JSON files instead of hardcoded dict
- Returns empty dict if configs not found

### 3. Updated `pyproject.toml`
```toml
[tool.setuptools.package-data]
"*" = ["*.json"]

[tool.setuptools]
include-package-data = true
```

### 4. New `MANIFEST.in`
```
recursive-include configs *.json
include README.md
include LICENSE
...
```

## Example Profiles Created

### Personal (GitHub)
```json
{
  "name": "default-personal",
  "mcp_servers": [
    {"name": "github", "enabled": true},
    {"name": "memory-bank", "enabled": true}
  ]
}
```

### Work (GitLab)
```json
{
  "name": "default-work",
  "mcp_servers": [
    {"name": "gitlab", "enabled": true},
    {"name": "k8s", "enabled": true},
    {"name": "atlassian", "enabled": true}
  ]
}
```

### DevOps (GitLab + Infra)
```json
{
  "name": "devops-gitlab",
  "mcp_servers": [
    {"name": "gitlab", "enabled": true},
    {"name": "k8s", "enabled": true},
    {"name": "heimdall", "enabled": true}
  ]
}
```

### QA (GitLab Read-Only + Testing)
```json
{
  "name": "qa-gitlab",
  "mcp_servers": [
    {"name": "gitlab", "enabled": true, "config": {"readOnly": true}},
    {"name": "cypress", "enabled": true}
  ]
}
```

### Researcher (Advanced AI)
```json
{
  "name": "researcher-advanced",
  "mcp_servers": [
    {"name": "duckduckgo", "enabled": true},
    {"name": "memory-bank", "enabled": true},
    {"name": "sequential-thinking", "enabled": true},
    {"name": "serena", "enabled": true}
  ]
}
```

## Adding New MCP Servers

Now it's as simple as:

1. Create `configs/mcp-servers/new-server.json`:
```json
{
  "name": "new-server",
  "description": "My new server",
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@myorg/mcp-server"]
}
```

2. Reinstall: `pip install -e .`

3. Done! No Python code changes needed.

## User Customization

Users can customize their local configs without affecting upgrades:

```bash
# Edit local copy
vim ~/.aidev/config/mcp-servers/gitlab.json

# Changes persist across aidev upgrades
# Original bundled config remains unchanged
```

## Migration Path

Existing installations:
1. Run `ai setup --force` to update with new JSON configs
2. Old hardcoded configs are replaced with JSON-based ones
3. User customizations in `~/.aidev/config/mcp-servers/custom/` are preserved

## Testing

```bash
# Reinstall with new configs
pip install -e /Users/churt/workspace/ai-developer

# Verify configs are bundled
ai setup --force

# List servers
ai mcp list

# Test a specific server
ai mcp test gitlab
```

## Benefits Realized

1. **Easier Maintenance**: Edit JSON files instead of Python code
2. **Better UX**: Non-developers can add MCP servers
3. **Cleaner Git History**: One file per server
4. **User Freedom**: Local customization without forking
5. **Simpler Reviews**: Smaller, focused PRs
6. **Better Documentation**: Each JSON file is self-documenting
7. **Faster Iteration**: No code recompilation needed

## Future Enhancements

- [ ] MCP server registry that points to these JSON configs
- [ ] Validation schema for JSON configs
- [ ] Auto-detection of installed MCP servers
- [ ] Template generator for new servers
- [ ] Web UI for editing configs

---

**Result**: Much cleaner, more maintainable design! 🎉
