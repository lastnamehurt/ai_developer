# aidev Architecture Overview

## Why `ai claude` vs just `claude`?

**The Problem**: Manually editing JSON configs for multiple tools, scattered env vars, no validation
**The Solution**: One profile → auto-configure all tools + validate + inject env vars

## Tool Launch Flow

```
$ ai claude
    │
    ├──────────────────────────┐
    ▼                          ▼
┌──────────────┐      ┌────────────────┐
│ Read profile │      │ Merge env vars │
│ .aidev/      │      │ global+project │
│ profile→web  │      └────────────────┘
└──────────────┘              │
    │                         │
    │  mcp_servers:[git,      │  GITHUB_TOKEN=xxx
    │   github,postgres]      │  DB_URL=yyy
    │                         │
    └─────────┬───────────────┘
              ▼
    ┌──────────────────────┐
    │ MCPConfigGenerator   │
    │ For each server:     │
    │  1. Load definition  │
    │  2. Expand ${VARS}   │
    │  3. Write config     │
    └──────────────────────┘
              │
              │ Writes ~/.claude.json (Claude global/local scope)
              │         ~/.codex/config.toml
              ▼
    ┌──────────────────────┐
    │ Preflight checks     │
    │  ✓ Env vars set?     │
    │  ✓ Binary exists?    │
    │  ✓ Config valid?     │
    └──────────────────────┘
              │
              ▼
      claude . (with full MCP context)
```

## Single Source of Truth

```
~/.aidev/config/profiles/web.json
{
  "mcp_servers": ["git", "github", "postgres"],
  "environment": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
}
       │
       │ ONE profile definition
       │
       ├─────────────────┬─────────────────┬──────────────────┐
       ▼                 ▼                 ▼                  ▼
~/.claude/         ~/.config/        ~/.codex/         ~/.gemini/
mcp.json           claude/           config.toml       settings.json
                   mcp.json

ALL tools stay in sync automatically
```

## Environment Variable Hierarchy

```
~/.aidev/.env           .aidev/.env
(global)                (project override)
    │                          │
    │ GITHUB_TOKEN=aaa         │ GITHUB_TOKEN=bbb ← wins
    │ API_KEY=xxx              │ DB_URL=postgres://
    │                          │
    └────────┬─────────────────┘
             ▼
      Merged environment
      GITHUB_TOKEN=bbb  ← project overrode global
      API_KEY=xxx       ← inherited from global
      DB_URL=postgres:// ← project-specific
```

## Components
- **CLI (`cli.py`)**: Click command tree (`ai`/`aidev`) for setup, quickstart, env, profile, mcp, tool launch, doctor, config TUI.
- **Config Manager (`config.py`)**: Initializes directories, merges global + project env, handles project init and tool config scaffolding.
- **Profiles (`profiles.py`)**: Built-in/custom profiles with tags and inheritance; save/load/merge utilities.
- **MCP (`mcp.py`)**: Registry fetch (with cache + bundled fallback), install/remove, connectivity testing, server config storage.
- **MCP Config Generator (`mcp_config_generator.py`)**: Emits MCP configs for tools (Cursor, Claude, Codex, Gemini, Zed) from profiles.
- **Errors/Preflight (`errors.py`)**: Centralized env/binary checks with actionable hints; used by `ai doctor`.
- **TUI (`tui_config.py`)**: Textual-based profile/env editor, loads project/active defaults.

## Data & Flows
- **Profiles**: JSON files in `~/.aidev/config/profiles` (+ `custom/`), referenced by `.aidev/profile` in projects.
- **Env**: Global `~/.aidev/.env` merged with project `.aidev/.env` (project overrides); commands support global/project scope.
- **MCP Registry**: Default URL overrideable via `AIDEV_MCP_REGISTRY`; caches to `~/.aidev/cache/mcp-registry.json`, falls back to `examples/mcp-registry.json` when offline.
- **Quickstart**: Detects JS/Python/Docker/K8s signals, recommends tag-based profile, initializes project config.
- **Doctor/Preflight**: Runs env/binary checks with hints; extendable for tool checks.

## Extending
- Add profiles: drop JSON into `~/.aidev/config/profiles/custom`.
- Add MCP servers: place JSON in `~/.aidev/config/mcp-servers/custom` or use `ai mcp install`.
- Add commands: extend `cli.py`, reuse managers for config/profile/env/MCP operations.
