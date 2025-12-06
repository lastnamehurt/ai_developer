# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aidev** is a universal, profile-based configuration manager for AI development tools (Cursor, Claude Code, Gemini, Codex). It centralizes MCP server configurations, environment variables, and tool launching across different projects and machines.

## Development Commands

### Setup & Installation
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the CLI locally (after installation)
aidev --version
ai --version  # alias
```

### Testing
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run specific test file
pytest tests/unit/test_profiles.py

# Run with coverage
pytest --cov=aidev --cov-report=html
pytest --cov=aidev --cov-report=term-missing
```

### Code Quality
```bash
# Format code (required before commits)
black src/ tests/

# Lint
ruff src/ tests/

# Type check
mypy src/
```

## Architecture

### Core Managers (modular design)
The codebase is organized around specialized manager classes:

- **ConfigManager** (`config.py`): Directory initialization, env variable merging (global `~/.aidev/.env` + project `.aidev/.env`), project initialization
- **ProfileManager** (`profiles.py`): Load/save profiles with inheritance (`extends` field), tag-based recommendation, built-in vs custom profiles
- **MCPManager** (`mcp.py`): MCP registry fetching (with cache + offline fallback), server installation/removal, connectivity testing
- **MCPConfigGenerator** (`mcp_config_generator.py`): Renders tool-specific MCP configs (Cursor, Claude, Codex, Gemini) from profile definitions
- **ToolManager** (`tools.py`): AI tool detection, config path resolution, tool launching with environment injection
- **QuickstartRunner** (`quickstart.py`): Stack detection (JS/Python/Docker/K8s), profile recommendation based on tags

### Data Models (`models.py`)
Uses Pydantic models for validation:
- `Profile`: name, description, extends, tags, mcp_servers, environment, tools
- `MCPServerConfig`: name, enabled, config overrides
- `MCPServerRegistry`: registry entry with install instructions, tags, compatible profiles
- `ToolInfo`: detected tool metadata (binary, config path, version)

### Configuration Hierarchy
1. **Global**: `~/.aidev/config/profiles/*.json`, `~/.aidev/.env`
2. **Custom**: `~/.aidev/config/profiles/custom/*.json`, `~/.aidev/config/mcp-servers/custom/*.json`
3. **Project**: `.aidev/config.json`, `.aidev/profile`, `.aidev/.env` (overrides global env)

### Profile Inheritance
Profiles can extend others via `extends` field. Merging logic in `ProfileManager._merge_profiles()`:
- Child MCP servers override/extend parent servers
- Child environment variables override parent
- Tags are merged (union)

### Tool Config Generation Flow
1. User runs `ai cursor --profile infra`
2. `ProfileManager.load_profile("infra")` loads profile + resolves inheritance
3. `MCPConfigGenerator.generate_config()` iterates profile's `mcp_servers`
4. For each server, fetches definition from `~/.aidev/config/mcp-servers/{name}.json`
5. Expands environment variables from global + project env
6. Writes tool-specific config format (JSON for Cursor/Claude, TOML for Codex)
7. `ToolManager.launch_tool()` executes tool binary with injected config

### MCP Registry & Caching
- **Remote**: Fetched from `AIDEV_MCP_REGISTRY` URL (default: configurable)
- **Cache**: Stored in `~/.aidev/cache/mcp-registry.json` (15-min TTL)
- **Fallback**: Bundled `examples/mcp-registry.json` used when offline

### Quickstart Stack Detection
`QuickstartDetector` scans project directory for signals:
- **JS**: `package.json`, `tsconfig.json`, `*.js` files
- **Python**: `pyproject.toml`, `requirements.txt`, `*.py` files
- **Docker**: `Dockerfile`, `docker-compose.yml`
- **K8s**: `*.yaml` with `kind: Deployment`, helm charts

Confidence scores aggregate to recommend profile by matching tags.

## Key Files

- `src/aidev/cli.py`: Click command tree (entry point)
- `src/aidev/config.py`: ConfigManager implementation
- `src/aidev/profiles.py`: ProfileManager with inheritance logic
- `src/aidev/mcp.py`: MCPManager with registry handling
- `src/aidev/mcp_config_generator.py`: Tool-specific MCP config rendering
- `src/aidev/quickstart.py`: Stack detection and profile recommendation
- `src/aidev/errors.py`: Preflight checks and error guidance (used by `ai doctor`)
- `src/aidev/tui_config.py`: Textual TUI for profile/env editing
- `src/aidev/models.py`: Pydantic data models
- `src/aidev/constants.py`: Path constants and defaults
- `src/aidev/utils.py`: Shared utilities (JSON/env file I/O, console)

## Testing Strategy

### Unit Tests (`tests/unit/`)
Test individual managers in isolation with mocked dependencies:
- `test_config_manager.py`: Directory init, env merging
- `test_profiles.py`: Profile loading, inheritance, merging
- `test_mcp.py`: Registry fetch, cache fallback
- `test_env_cli.py`: Env variable set/get/list commands
- `test_codex_mcp_config.py`, `test_gemini_mcp_config.py`: Tool-specific config generation

### Integration Tests (`tests/integration/`)
End-to-end workflows with temporary directories:
- `test_quickstart_flow.py`: Full quickstart + profile recommendation
- `test_profile_status_and_mcp_config.py`: Profile switching + MCP config generation
- `test_config_tui.py`: TUI load/save interactions

Use `tmp_path` fixture for isolated test environments. Clean up after each test.

## Common Patterns

### Adding a New MCP Server
1. Create JSON in `configs/mcp-servers/{name}.json` with schema:
   ```json
   {
     "command": "binary-name",
     "args": ["arg1", "arg2"],
     "env": {"KEY": "value"}
   }
   ```
2. Add entry to `examples/mcp-registry.json` (optional, for discoverability)
3. Reference in profile's `mcp_servers` array

### Adding a New Profile
1. Create JSON in `configs/profiles/custom/{name}.json`:
   ```json
   {
     "name": "my-profile",
     "description": "Description",
     "extends": "default",
     "tags": ["tag1", "tag2"],
     "mcp_servers": [
       {"name": "git", "enabled": true},
       {"name": "github", "enabled": true, "config": {"owner": "myorg"}}
     ],
     "environment": {
       "GITHUB_TOKEN": "${GITHUB_TOKEN}"
     }
   }
   ```
2. Use `ai profile list` to verify
3. Test with `ai use my-profile` in a project

### Adding a New AI Tool
1. Add entry to `configs/supported-tools.json`
2. Implement config generator in `MCPConfigGenerator` (e.g., `_write_xyz_config()`)
3. Add CLI command in `cli.py` (follow pattern of `cursor()`/`claude()`)
4. Update `ToolManager` if custom detection/launch logic needed

## Environment Variable Expansion
All MCP server `env` fields and profile `environment` values support `${VAR}` syntax:
- Resolved at config generation time via `utils.expand_env_vars()`
- Source: merged global + project env from `ConfigManager.get_env()`
- Missing vars log warnings but don't block (allows partial configs)

## Error Handling & Doctor
`errors.py` provides `preflight()` function for env/binary checks:
- Validates required env vars exist (e.g., `ANTHROPIC_API_KEY` for claude)
- Checks tool binaries on PATH
- Returns actionable error messages with fix hints
- Used by `ai doctor` command

## CI/CD
GitHub Actions workflow (`.github/workflows/tests.yml`):
- Runs on push/PR to `main`
- Python 3.11 on Ubuntu
- Executes `pytest tests/unit` and `pytest tests/integration`
- No coverage upload currently (can add with `pytest-cov`)

## Built-in Profiles
- **default**: Alias of `web`
- **web**: Web/app development (filesystem, git, github, memory-bank)
- **qa**: QA/testing (filesystem, git, duckduckgo, memory-bank)
- **infra**: Infrastructure/DevOps (filesystem, git, gitlab, k8s, atlassian)

Profiles use tags for quickstart matching (e.g., `["web", "javascript"]` for web profile).
