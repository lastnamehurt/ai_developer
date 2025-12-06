# aidev Architecture Overview

## Components
- **CLI (`cli.py`)**: Click command tree (`ai`/`aidev`) for setup, quickstart, env, profile, mcp, tool launch, doctor, config TUI.
- **Config Manager (`config.py`)**: Initializes directories, merges global + project env, handles project init and tool config scaffolding.
- **Profiles (`profiles.py`)**: Built-in/custom profiles with tags and inheritance; save/load/merge utilities.
- **MCP (`mcp.py`)**: Registry fetch (with cache + bundled fallback), install/remove, connectivity testing, server config storage.
- **MCP Config Generator (`mcp_config_generator.py`)**: Emits MCP configs for tools (Cursor, Claude, Codex, Gemini) from profiles.
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

## Diagram (high level)
```
CLI (Click)
 ├─ quickstart -> ConfigManager + ProfileManager + MCPManager
 ├─ env/profile/mcp/doctor -> ConfigManager + ProfileManager + MCPManager + Errors
 └─ tool launch -> MCPConfigGenerator -> tool configs

Storage
 ├─ ~/.aidev/.env (global) + project/.aidev/.env (override)
 ├─ ~/.aidev/config/profiles/*.json (+ custom/)
 ├─ ~/.aidev/config/mcp-servers/*.json (+ custom/)
 └─ ~/.aidev/cache/mcp-registry.json (with examples fallback)
```
