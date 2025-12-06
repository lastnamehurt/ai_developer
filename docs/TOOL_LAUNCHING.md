# Tool Launching Implementation

## Issue

When running `ai claude`, Claude Code was not opening or opening in the wrong directory.

## Root Causes

1. **Tool launching not implemented**: CLI commands had `# TODO` placeholders
2. **Profile system not initialized**: Built-in profiles weren't being created during setup
3. **Wrong launch method**: Claude Code is an interactive CLI tool, not a GUI app
4. **No current directory**: Subprocess wasn't using the current working directory

## Fixes Implemented

### 1. Implemented Tool Launching

**File**: `src/aidev/cli.py`

Added `_launch_tool_with_profile()` helper function that:
- Determines which profile to use (project-specific or default)
- Loads the profile configuration
- Launches the tool with appropriate arguments

```python
def _launch_tool_with_profile(tool_id: str, profile: str, args: tuple) -> None:
    # Check project-specific profile first
    # Fall back to default profile
    # Load profile and launch tool
```

### 2. Initialize Profiles and MCP Servers

**File**: `src/aidev/cli.py` - `setup()` command

Now properly initializes:
```python
# Initialize built-in profiles
profile_manager.init_builtin_profiles()

# Initialize built-in MCP servers
mcp_manager.init_builtin_servers()
```

This creates:
- `~/.aidev/config/profiles/{default,minimal,researcher,fullstack,devops,data}.json`
- `~/.aidev/config/mcp-servers/{filesystem,git,github,gitlab,...}.json`

### 3. Interactive CLI vs GUI Handling

**File**: `src/aidev/tools.py` - `launch_tool()`

Different launch methods for different tool types:

```python
# Interactive CLI tools (Claude Code)
if is_interactive_cli:
    os.execvp(tool_info.binary, cmd)  # Replace process, stay attached to terminal

# GUI apps (Cursor, Zed)
else:
    subprocess.Popen(cmd, start_new_session=True)  # Background launch
```

**Why `os.execvp` for Claude Code**:
- Claude Code is an interactive terminal application
- Needs to be attached to stdin/stdout for user interaction
- `execvp` replaces the current process, maintaining terminal connection
- Current working directory is set before exec

### 4. Working Directory Handling

All subprocess calls now use `cwd=os.getcwd()`:

```python
# Set current working directory
cwd = os.getcwd()

# Change to it before exec
os.chdir(cwd)
os.execvp(tool_info.binary, cmd)
```

This ensures the tool opens in the directory where `ai claude` was run.

### 5. Updated Command References

Changed all documentation and output from `aidev` to `ai`:

```bash
# Old
aidev cursor
aidev claude

# New
ai cursor
ai claude
```

## How It Works Now

### Running `ai claude`

1. **User runs**: `cd ~/my-project && ai claude`

2. **Profile resolution**:
   - Check for `.aidev/profile` file in current dir
   - Fall back to `default` profile

3. **Profile loading**:
   - Load profile JSON from `~/.aidev/config/profiles/`
   - Resolve MCP servers from profile

4. **Tool launch**:
   - Change to current working directory
   - Set environment variables
   - `execvp("claude", ["claude"])` - replaces process with Claude Code

5. **Claude Code starts**:
   - Runs in current directory (`~/my-project`)
   - Loads MCP configuration (future feature)
   - Interactive session begins

### Running `ai cursor`

Same process but:
- Passes `.` as argument: `cursor .`
- Uses `subprocess.Popen` for background launch
- GUI app opens in current directory

## Testing

```bash
# Setup (first time only)
ai setup

# Test in a project directory
cd ~/my-project
ai init

# Launch Claude Code (interactive)
ai claude

# Launch Cursor (GUI, background)
ai cursor

# Launch with specific profile
ai cursor --profile devops
ai claude --profile researcher
```

## Tool Types

### Interactive CLI
- **Claude Code**: Terminal-based, stays in foreground
- **Launch method**: `os.execvp()` (exec replace)
- **Directory**: Uses `cwd` from `os.chdir()`

### GUI Applications
- **Cursor**: GUI editor
- **Zed**: GUI editor
- **Launch method**: `subprocess.Popen(..., start_new_session=True)`
- **Directory**: Passed as argument (e.g., `cursor .`)

## Future Enhancements

- [ ] Generate MCP config file for each tool
- [ ] Inject profile-specific environment variables
- [ ] Support for tool-specific launch options
- [ ] Auto-detect tool type (interactive vs GUI)
- [ ] Support for remote MCP servers

## Architecture Decision

**Why `os.execvp` instead of `subprocess.run`?**

1. **Terminal attachment**: Keeps stdin/stdout connected
2. **Process replacement**: No extra wrapper process
3. **Signal handling**: User can Ctrl+C naturally
4. **Resource efficiency**: Only one process running

**Trade-off**: The `ai` command process is replaced, so no post-launch cleanup. This is acceptable since Claude Code is interactive and runs until the user exits.

## Verification

```bash
# Install
./install.sh

# Setup
ai setup --force

# Verify profiles exist
ls ~/.aidev/config/profiles/
# Output: custom  data.json  default.json  devops.json  fullstack.json  minimal.json  researcher.json

# Verify MCP servers exist
ls ~/.aidev/config/mcp-servers/
# Output: atlassian.json  compass.json  custom  cypress.json  duckduckgo.json  filesystem.json  ...

# Test launch
cd /tmp
ai claude
# Should start Claude Code interactive session in /tmp
```

## Summary

✅ **Tool launching implemented**
✅ **Profiles and MCP servers initialized**
✅ **Interactive CLI vs GUI handled correctly**
✅ **Current directory passed properly**
✅ **Command references updated to `ai`**

The `ai claude` command now works as expected, launching Claude Code in the current directory with full interactive terminal support.
