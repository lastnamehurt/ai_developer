### **Clarification: MCP Registry vs. Built-in Server Configurations**

There are two distinct mechanisms for discovering and configuring MCP servers in `aidev`:

1.  **The MCP Registry (for the `ai mcp browse` TUI)**
    -   **Source File:** The master list for the interactive TUI is `examples/mcp-registry.json`.
    -   **Purpose:** This file acts as a browsable "app store" for MCPs. It contains rich metadata like author, repository URL, and installation commands.
    -   **Behavior:** The application is designed to fetch this list from a central URL. The local `examples/mcp-registry.json` file serves as the **initial default and offline fallback** for the TUI. The modifications we have been making are to this file.

2.  **Built-in Server Configurations (this directory)**
    -   **Source Files:** The individual `*.json` files in this `src/aidev/configs/mcp-servers/` directory.
    -   **Purpose:** These files represent the pre-packaged, **runtime configurations** for a curated set of core servers that come bundled with `aidev`.
    -   **Behavior:** When you run `ai setup`, these files are copied to your local `~/.aidev/config/mcp-servers/` directory, so they are ready to be used immediately by a profile, without needing to be installed via the TUI.

In short, the **Registry (`examples/`)** is for discovering and installing new servers, while the **Built-in Configs (`configs/`)** are for providing a set of core, ready-to-use servers out of the box.

---

# aidev Configuration Files

This directory contains the built-in configuration files for aidev, stored as JSON for easy editing and management.

## Structure

```
configs/
└── mcp-servers/         # MCP server definitions
    ├── filesystem.json
    ├── git.json
    ├── github.json
    ├── gitlab.json
    ├── cypress.json
    ├── atlassian.json
    ├── k8s.json
    ├── serena.json
    ├── heimdall.json
    ├── compass.json
    ├── memory-bank.json
    ├── memory.json
    ├── sequential-thinking.json
    ├── duckduckgo.json
    └── postgres.json
```

## MCP Server Configuration Format

Each MCP server is defined in its own JSON file:

```json
{
  "name": "server-name",
  "description": "What this server does",
  "type": "stdio",
  "command": "command-to-run",
  "args": ["arg1", "arg2"],
  "env": {
    "ENV_VAR": "${ENV_VAR}"
  },
  "autoApprove": [
    "action1",
    "action2"
  ]
}
```

### Fields

- **name** (required): Unique identifier for the server
- **description** (required): Human-readable description
- **type** (required): Server type, usually "stdio"
- **command** (required): Command to execute
- **args** (optional): Array of command arguments
- **env** (optional): Environment variables with expansion support
- **autoApprove** (optional): Actions to auto-approve without prompting

### Variable Expansion

Environment variables support expansion syntax:
- `${VAR}` - Required variable, fails if not set
- `${VAR:-default}` - Optional variable with default value
- `${HOME}` - Standard environment variables

## Adding New MCP Servers

1. Create a new JSON file in `configs/mcp-servers/`
2. Follow the format above
3. Reinstall aidev: `pip install -e .`
4. The new server will be available after running `ai setup` again

Example - adding `redis.json`:

```json
{
  "name": "redis",
  "description": "Redis in-memory data store",
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@redis/mcp-server"],
  "env": {
    "REDIS_URL": "${REDIS_URL:-redis://localhost:6379}"
  }
}
```

## Modifying Existing Servers

To modify a server configuration:

1. Edit the JSON file directly in `configs/mcp-servers/`
2. No code changes needed!
3. Reinstall: `pip install -e .`
4. Run `ai setup --force` to update user installations

## Installation Behavior

When `ai setup` runs, it:

1. Looks for config files in `configs/mcp-servers/`
2. Copies them to `~/.aidev/config/mcp-servers/`
3. Does NOT overwrite existing user configs
4. User can customize their copies independently

## Benefits of This Design

✅ **No Code Changes**: Add/modify servers without touching Python
✅ **Easy to Read**: JSON is human-readable and editable
✅ **Version Control**: Track server config changes in git
✅ **User Override**: Users can customize their local copies
✅ **Distribution**: Configs are bundled with the package

## Common MCP Server Commands

| Command | Usage | Notes |
|---------|-------|-------|
| `npx -y <package>` | Install and run npm package | Most common for official servers |
| `uvx <package>` | Install and run Python package | For Python-based servers |
| `cargo install <package>` | Install Rust binary | For performance-critical servers |
| `node <path>` | Run local Node.js script | For custom/local servers |
| Custom binary | Direct execution | Must be in PATH |

## GitHub vs GitLab

The tool supports both git hosting platforms:

- **github.json**: For personal projects and GitHub workflows
- **gitlab.json**: For work projects and enterprise GitLab

Use profiles to switch between them:
```bash
ai cursor --profile default-personal  # Uses GitHub
ai cursor --profile default-work      # Uses GitLab
```

## Testing MCP Servers

After adding/modifying a server:

```bash
# List installed servers
ai mcp list

# Test connectivity
ai mcp test your-server-name

# View server config
cat ~/.aidev/config/mcp-servers/your-server-name.json
```

## Real-World Servers

All servers in this directory are production-ready and tested:

- **Official**: From @modelcontextprotocol (filesystem, memory, etc.)
- **Community**: From trusted maintainers (@zereight, @oraios, etc.)
- **Custom**: Project-specific tools (cypress, atlassian remote)

## Contributing

To contribute a new MCP server configuration:

11. Test the server locally
12. Create the JSON file following the format
13. Add documentation to the description field
14. Submit a PR with the new config file

---

**Note**: User modifications to `~/.aidev/config/mcp-servers/*.json` take precedence over bundled configs. This allows local customization without affecting upgrades.