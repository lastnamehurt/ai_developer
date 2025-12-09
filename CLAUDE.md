# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aidev** is a universal, profile-based configuration manager for AI development tools (Cursor, Claude Code, Zed, Gemini, Codex). It centralizes MCP server configurations, environment variables, and tool launching across different projects and machines.

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

# Run specific test function
pytest tests/unit/test_profiles.py::TestProfileManager::test_create_profile

# Run with coverage report (terminal)
pytest --cov=aidev --cov-report=term-missing

# Run with coverage report (HTML)
pytest --cov=aidev --cov-report=html
```

### Code Quality
```bash
# Format code (required before commits)
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Architecture

### Core Managers (modular design)
The codebase is organized around specialized manager classes:

- **ConfigManager** (`config.py`): Directory initialization, env variable merging (global `~/.aidev/.env` + project `.aidev/.env`), project initialization
- **ProfileManager** (`profiles.py`): Load/save profiles with inheritance (`extends` field), tag-based recommendation, built-in vs custom profiles
- **MCPManager** (`mcp.py`): MCP registry fetching (with cache + offline fallback), server installation/removal, connectivity testing
- **MCPConfigGenerator** (`mcp_config_generator.py`): Renders tool-specific MCP configs (Cursor, Claude, Codex, Gemini, Zed) from profile definitions
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

### Workflow System (`workflow.py`)
The workflow engine orchestrates multi-step AI tasks by coordinating assistant execution. It uses a minimal, declarative schema where workflows define *what* to do, and the engine handles *how* to do it.

#### Smart Engine Behavior
- **Smart Issue Detection**: The engine automatically detects Jira, GitHub, and GitLab issue/MR references from the input text. The `uses_issue_mcp` flag is no longer needed.
- **Profile-Agnostic Workflows**: Workflows are no longer tied to specific profiles. The active profile is resolved at runtime.
- **Implicit File Handling**: The engine accepts files when relevant, removing the need for `allow_file` flags.

#### Handoff Mechanism
When users run `ai workflow <name> <input>`:
1. Workflow manifest is generated at `.aidev/workflow-runs/<name>-<timestamp>.json`
2. The manifest includes a `detected_issue_context` field with details about any detected issue.
3. Assistant is launched with instruction to read the manifest file (not raw content)
4. Command example: `claude --system-prompt "You are a workflow executor..." "Read and execute the workflow manifest at: /path/to/manifest.json"`
5. Assistant uses Read tool to access manifest and execute steps

**Key Design Decision**: File path reference instead of raw manifest content avoids:
- Command-line argument length limits
- Excessive token usage in initial prompt
- Escaping/encoding issues with large JSON payloads

#### Adding Support for New Assistants
To add a new assistant to the workflow system:
1. Update `_assistant_command()` in `workflow.py`:
   ```python
   if assistant == "newtool":
       return _cmd("newtool", ["--flag", prompt_text])
   ```
2. Follow the pattern: prioritize non-interactive/one-shot modes
3. Avoid stdin piping for TUI-based tools (preserves raw terminal mode)
4. Test both `execute_manifest()` (automated) and `handoff_to_assistant()` (interactive)

## Key Files

### Core Functionality
- `src/aidev/cli.py`: Click command tree (entry point)
- `src/aidev/config.py`: ConfigManager implementation
- `src/aidev/profiles.py`: ProfileManager with inheritance logic
- `src/aidev/mcp.py`: MCPManager with registry handling
- `src/aidev/mcp_config_generator.py`: Tool-specific MCP config rendering
- `src/aidev/tools.py`: ToolManager for AI tool detection, config resolution, and launching
- `src/aidev/workflow.py`: Workflow engine, assistant resolver, and command execution
- `src/aidev/errors.py`: Preflight checks and error guidance (used by `ai doctor`)

### Data & Configuration
- `src/aidev/models.py`: Pydantic data models
- `src/aidev/constants.py`: Path constants and defaults
- `src/aidev/secrets.py`: Environment variable encryption/decryption
- `src/aidev/utils.py`: Shared utilities (JSON/env file I/O, console)

### User Interfaces & Features
- `src/aidev/tui_config.py`: Textual TUI for profile/env editing
- `src/aidev/tui_mcp_browser.py`: Textual TUI for browsing and managing MCP servers
- `src/aidev/quickstart.py`: Stack detection and profile recommendation
- `src/aidev/review.py`: Code review functionality
- `src/aidev/backup.py`: Configuration backup and restore utilities

## Testing Strategy

### Unit Tests (`tests/unit/`)
Test individual managers in isolation with mocked dependencies. Run with:
```bash
pytest tests/unit
pytest tests/unit/test_profiles.py::TestProfileManager::test_create_profile
```

Test coverage includes:
- `test_config_manager.py`: Directory init, env merging, config file I/O
- `test_profiles.py`: Profile loading, inheritance, merging logic
- `test_mcp.py`: Registry fetch, cache fallback, offline handling
- `test_env_cli.py`: Env variable set/get/list commands, encryption
- `test_codex_mcp_config.py`, `test_gemini_mcp_config.py`: Tool-specific config generation
- Other tool config tests: Cursor, Claude, Zed MCP config rendering

### Integration Tests (`tests/integration/`)
End-to-end workflows with temporary directories testing real interactions:
- `test_quickstart_flow.py`: Full quickstart + profile recommendation
- `test_profile_status_and_mcp_config.py`: Profile switching + MCP config generation
- `test_config_tui.py`: TUI load/save interactions

Run with:
```bash
pytest tests/integration
```

**Best Practices:**
- Use `tmp_path` fixture (pytest) for isolated test environments
- Mock external calls (HTTP requests to MCP registry, tool binary execution)
- Clean up after each test; don't rely on test execution order
- Ensure tests pass on Python 3.10, 3.11, and 3.12 (tested in CI)

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
- Use `ai env set KEY value` or `ai env set KEY value --project` to manage vars

## Error Handling & Doctor
`errors.py` provides `preflight()` function for env/binary checks:
- Validates required env vars exist (e.g., `ANTHROPIC_API_KEY` for claude)
- Checks tool binaries on PATH
- Returns actionable error messages with fix hints
- Used by `ai doctor` command

## Important Implementation Details

### Encryption & Secrets
- Environment variables can be encrypted with `ai env set --encrypt KEY value`
- Encrypted values are prefixed with `ENC::` and stored in `.env` files
- Encryption key is stored in `~/.aidev/.env.key` (mode 0o600)
- `secrets.py` handles encryption/decryption using Fernet (cryptography library)
- Always validate that sensitive data is properly encrypted before committing

### Backup & Restore
- `backup.py` manages configuration migration between machines
- Backups are tar.gz archives with metadata manifest
- Used by `ai backup` and `ai restore` commands
- Includes profiles, MCP configs, and encrypted environment variables

### Config File Format
Configuration uses JSON for profiles and MCP servers, but:
- Workflows are defined in YAML (`.aidev/workflows.yaml`)
- Environment variables in `.env` (key=value format)
- MCP registry is JSON with metadata for discovery
- Tool-specific configs are generated in their native formats (JSON/TOML)

### Path Constants
All path operations use `constants.py` definitions:
- `AIDEV_DIR` = `~/.aidev/` (global config root)
- `PROFILES_DIR` = `~/.aidev/config/profiles/` (built-in)
- `CUSTOM_PROFILES_DIR` = `~/.aidev/config/profiles/custom/` (user-defined)
- `PROJECT_AIDEV_DIR` = `./.aidev/` in current project
- Use these constants instead of hardcoding paths

## CI/CD
GitHub Actions workflow (`.github/workflows/tests.yml`):
- Runs on push/PR to `main`
- Python 3.11 on Ubuntu
- Executes `pytest tests/unit` and `pytest tests/integration` sequentially
- Must pass all tests before PR merge
- Coverage reports available locally with `pytest --cov=aidev --cov-report=html`

Before committing, ensure:
```bash
pytest                  # All tests pass
black src/ tests/       # Code formatted
ruff check src/ tests/  # No lint issues
mypy src/               # Type hints valid
```

## Setup Process & Environment Variables

### New User Setup
When users install aidev, the `ai setup` command now includes interactive prompts for required environment variables:

1. **Initial setup** creates directories and profiles
2. **Profile selection** - users choose which profiles to configure (web, infra, or both)
3. **Environment variable prompts** - for each profile, users are prompted for required secrets:
   - **web profile**: `GITHUB_TOKEN` or `GITHUB_PERSONAL_ACCESS_TOKEN`
   - **infra profile**: `GITLAB_PERSONAL_ACCESS_TOKEN` and optionally `GITLAB_URL`
   - Users see helpful links to where to get each secret (GitHub settings, GitLab settings, etc.)
4. **Encryption** - sensitive values are automatically encrypted and stored in `~/.aidev/.env`

### Required Environment Variables by Profile
Built-in mapping in `src/aidev/env_requirements.py`:
- **web**: github (requires `GITHUB_TOKEN`)
- **qa**: duckduckgo (no secrets required)
- **infra**: gitlab (requires `GITLAB_PERSONAL_ACCESS_TOKEN`), k8s (optional `KUBECONFIG`)
- **postgres**: requires `POSTGRES_URL`

Users can add more env vars with `ai env set KEY value [--project] [--encrypt]`

### Health Checks
The `ai doctor` command now:
1. Checks if all required env vars for the active profile are set
2. Shows which are missing with links to where to get them
3. Provides actionable error messages

## Getting Started with Development

### First Time Setup
1. Clone and install dev dependencies:
   ```bash
   git clone https://github.com/lastnamehurt/ai_developer.git
   cd ai_developer
   pip install -e ".[dev]"
   ```

2. Verify installation:
   ```bash
   ai --version
   pytest tests/unit -k test_config_manager --no-cov  # Quick sanity check
   ```

3. Run all tests to ensure environment is correct:
   ```bash
   pytest
   ```

### Development Workflow
1. **Make changes** to files in `src/aidev/`
2. **Run tests** for the affected module:
   ```bash
   pytest tests/unit/test_profiles.py -v --no-cov
   ```
3. **Format and lint** before committing:
   ```bash
   black src/ tests/
   ruff check src/ tests/ --fix
   mypy src/
   ```
4. **Run full test suite** before pushing:
   ```bash
   pytest
   ```

### Common Development Tasks

**Debugging a failing test:**
```bash
pytest tests/unit/test_mcp.py::TestMCPManager::test_registry_fetch -vvs
# -vvs: verbose, very verbose, no capture (see print statements)
```

**Testing a specific manager:**
```bash
# Test ConfigManager's env merging logic
pytest tests/unit/test_config_manager.py -v

# Test ProfileManager's inheritance
pytest tests/unit/test_profiles.py::TestProfileManager::test_profile_inheritance -v
```

**Adding a new test:**
- Follow the pattern in existing test files (use `tmp_path` fixture for isolation)
- Name test functions `test_<feature_being_tested>`
- Test both success and failure cases
- Mock external dependencies (HTTP requests, file system operations outside tmp_path)

### Troubleshooting Development

**Import errors when running tests:**
- Ensure you ran `pip install -e ".[dev]"` (with editable install flag)
- Delete any `__pycache__` directories: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`

**Type checking failures:**
- Check that function signatures match their implementations
- Use `from __future__ import annotations` for forward references
- Run `mypy src/ --no-incremental` to get fresh analysis

**Tests pass locally but fail in CI:**
- Ensure tests don't depend on local machine state (use `tmp_path`)
- Don't hardcode absolute paths (use `constants.py`)
- Test on Python 3.11 (what CI uses): `python3.11 -m pytest`

## Built-in Profiles
- **default**: Alias of `web`
- **web**: Web/app development (filesystem, git, github, memory-bank)
- **qa**: QA/testing (filesystem, git, duckduckgo, memory-bank)
- **infra**: Infrastructure/DevOps (filesystem, git, gitlab, k8s, atlassian)

Profiles use tags for quickstart matching (e.g., `["web", "javascript"]` for web profile).
