# aidev Workflow System Overview

This doc explains how an aidev workflow command flows from the user to a run manifest and (optionally) into execution. Use it as a quick map of the CLI, core engine, and the artifacts they produce.

## Quick Flow
1) User runs `aidev workflow <workflow_name>` with flags like `--ticket`, `--file`, or `--execute`.
2) `src/aidev/cli.py` parses CLI arguments and hands them to `workflow()`.
3) `workflow()` instantiates `WorkflowEngine` (in `src/aidev/workflow.py`).
4) `WorkflowEngine` loads workflow definitions from `workflows.yaml`, resolves `WorkflowSpec` and `WorkflowStep` objects, and associates prompt files from `src/aidev/prompts/`.
5) `run_workflow()` produces a run manifest in `.aidev/workflow-runs/` capturing the resolved steps, inputs, and placeholders for execution output.
6) If `--execute` is provided, the CLI calls `execute_manifest()` (currently conceptual/placeholder) to perform the steps and fill in results.

## System Diagram
```
                                   +----------------------+
                                   |  User Interaction    |
                                   +----------------------+
                                              |
                                              | aidev workflow <args>
                                              V
                           +-------------------------------+
                           | CLI Layer (src/aidev/cli.py)  |
                           +-------------------------------+
                                      |
                                      | parses args and calls workflow()
                                      V
                     +--------------------------------------------+
                     | WorkflowEngine (src/aidev/workflow.py)    |
                     +--------------------------------------------+
                                      |
                                      | loads workflows.yaml
                                      | -> WorkflowSpec -> WorkflowStep
                                      | -> prompt files (src/aidev/prompts/)
                                      V
                +---------------------------------------------------+
                | Run Manifest (.aidev/workflow-runs/<name>-<ts>.json) |
                | - workflow name and inputs (--ticket/--file/etc.) |
                | - steps: assistant, prompt text, tool config      |
                | - execution outputs: status/result placeholders   |
                +---------------------------------------------------+
                                      |
                                      | if --execute flag is present
                                      V
                     +--------------------------------------------+
                     | execute_manifest() (placeholder)           |
                     | reads manifest, performs steps, writes     |
                     | status/result back to manifest             |
                     +--------------------------------------------+
```

## Component Responsibilities
- **CLI (src/aidev/cli.py)**: Parses arguments (`workflow_name`, `--ticket`, `--file`, `--execute`, timeouts) and delegates to `workflow()`.
- **WorkflowEngine (src/aidev/workflow.py)**: Loads `workflows.yaml`, constructs `WorkflowSpec`/`WorkflowStep`, resolves prompt text, and orchestrates manifest creation through `run_workflow()`.
- **Prompt files (src/aidev/prompts/)**: Text templates referenced by steps for assistant instructions.
- **Run manifest (.aidev/workflow-runs/*.json)**: Captures the selected workflow, inputs, resolved steps (assistant, prompt, tool options, timeout, retries), and execution outputs (`status`, `result`).
- **execute_manifest()**: Conceptual entry point for actually executing steps when `--execute` is supplied; currently a placeholder.

## Notes and Limitations
- The manifest format is the source of truth for what will run; it is safe to inspect or archive for auditing.
- `execute_manifest()` is not fully implemented; any execution semantics should be validated before relying on it in automation.
