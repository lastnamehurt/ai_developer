# Workflow System

The workflow system in `aidev` allows you to orchestrate multi-step AI tasks across different assistants. Workflows are defined in YAML and can be executed interactively or automated.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Workflow Definitions](#workflow-definitions)
- [Execution Modes](#execution-modes)
- [Supported Assistants](#supported-assistants)
- [Assistant Handoff Mechanism](#assistant-handoff-mechanism)
- [Creating Custom Workflows](#creating-custom-workflows)
- [Troubleshooting](#troubleshooting)

## Overview

Workflows enable you to:
- Break down complex tasks into discrete steps
- Use different AI assistants for different steps
- Define system prompts and inputs for each step
- Execute steps interactively or automatically
- Resume execution from a specific step
- Configure retries and timeouts per step

## Quick Start

```bash
# List available workflows
ai workflow list

# Run a workflow with a ticket/input
ai workflow doc_improver README.md

# Execute workflow non-interactively
ai workflow doc_improver README.md --execute

# Resume from a specific step
ai workflow doc_improver README.md --from-step "Review changes"

# Use a specific assistant
ai workflow doc_improver README.md --tool claude
```

## Workflow Definitions

Workflows are defined in `.aidev/workflows.yaml`:

```yaml
workflows:
  doc_improver:
    description: "Improve documentation quality"
    input:
      kind: text          # text, jira, github, file
      allow_file: true    # Allow file input
    tool: claude          # Default assistant (optional)
    steps:
      - name: "Analyze content"
        profile: default
        prompt: analyze_docs    # References src/aidev/prompts/analyze_docs.txt
        timeout_sec: 60
        retries: 1

      - name: "Generate improvements"
        profile: default
        prompt: improve_docs
        tool: gemini        # Override default assistant
        uses_issue_mcp: false
```

### Workflow Fields

- **name**: Unique workflow identifier
- **description**: Human-readable description
- **input.kind**: Input type (`text`, `jira`, `github`, `file`, `raw`)
- **input.allow_file**: Whether to accept file inputs
- **tool**: Default assistant for all steps (optional)
- **steps**: Array of workflow steps

### Step Fields

- **name**: Step name (for logging and resume)
- **profile**: Profile to use for this step
- **prompt**: Prompt file ID (from `src/aidev/prompts/`)
- **tool**: Assistant override for this step (optional)
- **timeout_sec**: Execution timeout (default: 30)
- **retries**: Number of retry attempts (default: 0)
- **uses_issue_mcp**: Whether step needs issue MCP integration

## Execution Modes

### 1. Interactive Handoff (Default)

When you run a workflow without `--execute`, it prepares a manifest and hands off to an assistant CLI:

```bash
ai workflow doc_improver README.md
```

**What happens:**
1. Manifest JSON is created in `.aidev/workflow-runs/doc_improver-<timestamp>.json`
2. Assistant CLI is launched with instruction to read the manifest
3. You interact with the assistant as it executes steps
4. Assistant can ask questions and adapt execution

**Example command executed:**
```bash
claude --system-prompt "You are a workflow executor. Read the manifest JSON file and execute the steps sequentially..." \
  "Read and execute the workflow manifest at: /path/to/manifest.json"
```

### 2. Automated Execution

With `--execute`, steps run non-interactively:

```bash
ai workflow doc_improver README.md --execute
```

**What happens:**
1. Manifest is created
2. Each step runs automatically via assistant CLI
3. Output is captured and stored in manifest
4. Process continues until completion or error
5. Steps respect retry/timeout settings

### 3. Resume from Step

Continue execution from a specific step:

```bash
ai workflow doc_improver README.md --from-step "Generate improvements"
```

Useful when:
- A step fails and you want to retry after fixing issues
- You want to skip early steps
- Testing individual workflow steps

### 4. Single Step Execution

Run only the first step:

```bash
ai workflow doc_improver README.md --step-only
```

## Supported Assistants

The workflow system supports multiple AI assistants with specific invocation patterns:

### Claude (Anthropic)

**Command format:** `claude --system-prompt <system> <user_input>`

- Uses `--system-prompt` flag for workflow instructions
- User input as positional argument
- No stdin piping (preserves terminal raw mode for TUI)

**Example:**
```bash
claude --system-prompt "You are a code reviewer..." "Review the code in src/main.py"
```

**Notes:**
- Best for interactive workflows
- Supports full terminal UI features
- Recommended for complex multi-step tasks

### Codex

**Command format:** `codex exec <prompt>`

- Uses `exec` subcommand for non-interactive mode
- Positional prompt argument
- Optimized for one-shot execution

**Example:**
```bash
codex exec "Analyze this code and suggest improvements: $(cat file.py)"
```

**Notes:**
- Fast for automated workflows
- Use `exec` to avoid interactive mode
- Good for code-focused tasks

### Gemini (Google)

**Command format:** `gemini <prompt>`

- Positional prompt defaults to one-shot mode
- No special flags needed
- Simple invocation pattern

**Example:**
```bash
gemini "Summarize these requirements and create a task list"
```

**Notes:**
- Clean one-shot execution
- Good for text processing tasks
- Fast response times

### Ollama (Local LLMs)

**Command format:** `ollama run llama3.1 --prompt <prompt>`

- Requires model specification (`llama3.1`)
- Uses `--prompt` flag
- Runs locally

**Example:**
```bash
ollama run llama3.1 --prompt "Explain this error message..."
```

**Notes:**
- Fully local execution
- No API costs
- Requires local model installation

### Cursor

**Status:** Not supported (no headless/CLI mode available)

## Assistant Handoff Mechanism

### Design Philosophy

The handoff mechanism passes a **file path reference** instead of raw manifest content to avoid:

- **Command-line length limits**: Manifests can be large (10KB+)
- **Token overhead**: No need to include full manifest in initial prompt
- **Escaping issues**: JSON special characters don't need escaping
- **Better UX**: Assistant can re-read manifest as needed

### How It Works

1. **Manifest Creation**
   ```
   .aidev/workflow-runs/doc_improver-20251208-103154.json
   ```

2. **Assistant Launch**
   ```bash
   claude --system-prompt "You are a workflow executor. Read the manifest JSON file and execute the steps sequentially. Use the system prompt as given and the user prompt/ticket content as input. Narrate your actions and produce outputs per step." \
     "Read and execute the workflow manifest at: /Users/user/project/.aidev/workflow-runs/doc_improver-20251208-103154.json"
   ```

3. **Assistant Execution**
   - Assistant uses Read tool to access manifest
   - Parses workflow steps and metadata
   - Executes each step sequentially
   - Can interact with user for clarifications

### Technical Details

**subprocess Configuration:**
```python
# Don't pipe stdin for TUI CLIs - preserves raw terminal mode
proc = subprocess.Popen(cmd, text=True, start_new_session=True)
```

**Why no stdin piping?**
- TUI assistants (like Claude) need raw terminal mode
- Piped stdin causes "Raw mode not supported" errors
- `start_new_session=True` prevents terminal control conflicts

## Creating Custom Workflows

### Step 1: Define the Workflow

Edit `.aidev/workflows.yaml`:

```yaml
workflows:
  my_workflow:
    description: "My custom workflow"
    input:
      kind: text
      allow_file: true
    steps:
      - name: "Step 1"
        profile: default
        prompt: my_prompt
        timeout_sec: 120
```

### Step 2: Create Prompt Files

Create `src/aidev/prompts/my_prompt.txt`:

```
You are a helpful assistant tasked with [specific task].

Given the following input, please:
1. [instruction 1]
2. [instruction 2]
3. [instruction 3]

Be concise and actionable in your output.
```

### Step 3: Test the Workflow

```bash
# Test interactively first
ai workflow my_workflow "test input"

# Then test automated execution
ai workflow my_workflow "test input" --execute
```

### Best Practices

1. **Keep steps focused**: Each step should have a single responsibility
2. **Set appropriate timeouts**: Complex tasks need longer timeouts
3. **Use retries sparingly**: Only for transient failures (network, etc.)
4. **Test with different assistants**: Each has strengths/weaknesses
5. **Document prompts clearly**: Include examples and expected outputs
6. **Version control workflows**: Track changes to `workflows.yaml`

## Troubleshooting

### "Raw mode is not supported" Error

**Cause:** stdin piping interferes with TUI assistants

**Solution:** This is fixed in the latest version. If you still see it:
1. Update `aidev` to latest version
2. Check that you're not piping input: `ai workflow ... < file` (don't do this)

### "Unknown option --prompt" Error (Claude)

**Cause:** Claude CLI doesn't support `--prompt` flag

**Solution:** Fixed - we now use positional arguments instead

### Workflow Hangs on Execution

**Possible causes:**
- Timeout too long, process still running
- Assistant waiting for input
- Network connectivity issues

**Solutions:**
```bash
# Use shorter timeout
timeout_sec: 30  # in workflow definition

# Check process
ps aux | grep claude

# Kill if needed
pkill claude
```

### Step Fails with Timeout

**Solutions:**
1. Increase `timeout_sec` in workflow definition
2. Simplify the step prompt
3. Split into multiple smaller steps
4. Use a faster assistant (e.g., Gemini for simple tasks)

### Manifest Not Found

**Cause:** Workflow runs directory doesn't exist

**Solution:**
```bash
# Manifests are in:
ls .aidev/workflow-runs/

# Manually create if needed:
mkdir -p .aidev/workflow-runs/
```

### Assistant Not Available

**Error:** `No runner available for assistant 'xyz'`

**Solutions:**
1. Install the assistant CLI
2. Ensure it's on your PATH
3. Specify a different assistant: `--tool claude`
4. Check installed assistants: `which claude gemini codex`

## Advanced Usage

### Custom Assistant Resolution

Assistant priority order:
1. CLI `--tool` flag
2. Step-level `tool` field
3. Workflow-level `tool` field
4. `AIDEV_DEFAULT_ASSISTANT` environment variable
5. Project default assistant
6. Fallback: claude → codex → cursor → gemini → ollama

### Environment Variables

```bash
# Set default assistant globally
export AIDEV_DEFAULT_ASSISTANT=gemini

# Then run workflow (uses gemini unless overridden)
ai workflow doc_improver README.md
```

### Manifest Schema

Manifests are JSON with this structure:

```json
{
  "workflow": "doc_improver",
  "description": "Improve documentation quality",
  "schema_version": "1.1",
  "ticket_source": "file",
  "ticket_arg": null,
  "ticket_file": "README.md",
  "created_at": 1702053154,
  "completed_at": null,
  "steps": [
    {
      "name": "Analyze content",
      "profile": "default",
      "prompt_id": "analyze_docs",
      "prompt_text": "...",
      "assistant": "claude",
      "uses_issue_mcp": false,
      "tool_timeout_sec": 60,
      "retries": 1,
      "input": {
        "ticket_source": "file",
        "ticket_text_preview": "...",
        "user_prompt": "..."
      },
      "output": {
        "status": "not-run",
        "result": null
      }
    }
  ]
}
```

### Programmatic Access

```python
from aidev.workflow import WorkflowEngine
from pathlib import Path

# Load and run workflow
engine = WorkflowEngine(Path.cwd())
workflows, warnings = engine.load_workflows()

# Get specific workflow
workflow = workflows['doc_improver']

# Execute
manifest_path = engine.run_workflow(
    workflow,
    ticket="Improve README",
    ticket_file=None,
    user_prompt=None,
    tool_override="claude"
)

# Execute manifest
engine.execute_manifest(manifest_path)
```

## See Also

- [Workflow System Diagram](./workflow_system_diagram.md) - ASCII architecture diagram
- [Commands Reference](./commands.md) - All CLI commands
- [Profiles](./profiles.md) - Profile system documentation
