# WorkflowManifest Helper Guide

## Overview

The `WorkflowManifest` helper class makes it easy for workflow executors to safely and incrementally update workflow manifests as steps complete.

**Problem it solves:** Previously, executors had to manually edit JSON manifest files to update step status and results. This was error-prone and could result in updates being batched at the end instead of happening incrementally.

**Solution:** The `WorkflowManifest` class provides a clean API for updating manifests step-by-step.

## Installation

The class is built into `aidev` and can be imported directly:

```python
from aidev import WorkflowManifest
```

## Quick Start

```python
from aidev import WorkflowManifest

# Load the manifest
manifest = WorkflowManifest('/path/to/manifest.json')

# After executing each step, mark it complete
manifest.mark_step_complete('step_name', 'Summary of what was accomplished')

# That's it! The manifest is saved automatically
```

## Core Methods

### `mark_step_complete(step_name, result, status='ok', save=True)`

Mark a step as complete immediately after it finishes executing.

**Parameters:**
- `step_name` (str): Name of the step (must match manifest)
- `result` (str): Summary of what was accomplished
- `status` (str): Status code, defaults to `'ok'`
- `save` (bool): Save to disk immediately (default: True)

**Example:**
```python
manifest = WorkflowManifest(manifest_path)
result = execute_detect_branches()
manifest.mark_step_complete('detect_branches', result)
```

### `mark_step_failed(step_name, error, save=True)`

Mark a step as failed with error details.

**Parameters:**
- `step_name` (str): Name of the step that failed
- `error` (str): Error message or summary
- `save` (bool): Save to disk immediately

**Example:**
```python
try:
    result = execute_rebase()
    manifest.mark_step_complete('fetch_and_rebase', result)
except Exception as e:
    manifest.mark_step_failed('fetch_and_rebase', f'Merge conflict: {e}')
```

### `validate() -> list[str]`

Check which steps have not yet been completed.

**Returns:** List of incomplete step names (empty if all done)

**Example:**
```python
incomplete = manifest.validate()
if incomplete:
    raise RuntimeError(f"Incomplete steps: {incomplete}")
```

### `get_completed_steps() -> list[str]`

Get names of all completed steps.

**Example:**
```python
completed = manifest.get_completed_steps()
print(f"Completed {len(completed)} of {len(manifest.get_all_steps())} steps")
```

### `get_failed_steps() -> list[str]`

Get names of all failed steps.

**Example:**
```python
failed = manifest.get_failed_steps()
if failed:
    print(f"Failed steps: {', '.join(failed)}")
```

### `get_all_steps() -> list[dict]`

Get all step configurations.

**Example:**
```python
for step in manifest.get_all_steps():
    print(f"Step: {step['name']}")
```

### `get_step(step_name) -> dict | None`

Get a specific step's configuration.

**Example:**
```python
step = manifest.get_step('detect_branches')
if step:
    print(step['prompt_text'])
```

### `batch_update(updates)`

Update multiple steps at once. ⚠️ Use sparingly - incremental updates are preferred.

**Parameters:**
- `updates` (dict): {step_name: result_string}

**Example:**
```python
# Not recommended, but available if needed
manifest.batch_update({
    'step_one': 'result 1',
    'step_two': 'result 2',
})
```

## Recommended Usage Pattern

The **recommended pattern** is to update the manifest immediately after EACH step completes, not at the end:

```python
from aidev import WorkflowManifest

def execute_workflow(manifest_path):
    manifest = WorkflowManifest(manifest_path)

    for step in manifest.get_all_steps():
        step_name = step['name']
        print(f"Executing {step_name}...")

        try:
            # Execute the step (pseudo-code)
            result = execute_step(step)

            # UPDATE IMMEDIATELY - Key principle!
            manifest.mark_step_complete(step_name, result)
            print(f"✓ {step_name} complete")

        except Exception as e:
            # Mark as failed
            manifest.mark_step_failed(step_name, str(e))
            print(f"✗ {step_name} failed: {e}")
            raise

    print("✓ All steps completed!")
```

### ✅ DO

- Call `mark_step_complete()` immediately after a step finishes
- Call `mark_step_failed()` when a step fails
- Call `validate()` at the end to ensure all steps completed
- Use descriptive result summaries

### ❌ DON'T

- Batch all updates at the end
- Forget to update the manifest
- Manually edit the JSON file
- Update with empty or unclear summaries

## Error Handling

The class raises clear errors for common mistakes:

```python
manifest = WorkflowManifest(manifest_path)

# ValueError: Step not found
manifest.mark_step_complete('nonexistent_step', 'result')

# FileNotFoundError: Manifest doesn't exist
manifest = WorkflowManifest('/nonexistent/path.json')

# ValueError: Invalid JSON in manifest
# (caught when loading)
```

## Progress Tracking

Use the helper to track and display progress:

```python
manifest = WorkflowManifest(manifest_path)
total = len(manifest.get_all_steps())

for i, step in enumerate(manifest.get_all_steps(), 1):
    progress = f"[{i}/{total}]"
    print(f"{progress} Executing {step['name']}...")

    result = execute_step(step)
    manifest.mark_step_complete(step['name'], result)
    print(f"{progress} ✓ Done")

# Final status
print(f"\nCompleted: {len(manifest.get_completed_steps())}")
print(f"Failed: {len(manifest.get_failed_steps())}")
```

## Manifest Structure

The manifest JSON has this structure:

```json
{
  "workflow": "sync_branch",
  "description": "Rebase branch onto target",
  "steps": [
    {
      "name": "detect_branches",
      "output": {
        "status": "not-run",
        "result": null
      }
    },
    {
      "name": "fetch_and_rebase",
      "output": {
        "status": "ok",
        "result": "Rebase completed successfully with no conflicts"
      }
    }
  ]
}
```

The helper class manages the `output.status` and `output.result` fields automatically.

## Testing

All functionality is covered by comprehensive tests:

```bash
pytest src/aidev/test_workflow_manifest.py -v
```

Tests verify:
- ✓ Marking steps complete
- ✓ Marking steps failed
- ✓ Validation logic
- ✓ Getting step status
- ✓ Batch updates
- ✓ Error handling
- ✓ File I/O

## Integration with Claude Code

When Claude Code executes a workflow, it receives this instruction:

```
IMPORTANT: After completing EACH step, update the manifest JSON file immediately.

TIP: Use the WorkflowManifest helper for safe and easy updates:
  from aidev import WorkflowManifest
  manifest = WorkflowManifest(manifest_path)
  manifest.mark_step_complete('step_name', 'Result summary')
```

This ensures executors know to use the helper and update incrementally.

## Examples

See full working examples in:
- `src/aidev/examples/workflow_manifest_usage.py`

## Benefits

1. **Type-safe**: Python object instead of raw JSON editing
2. **Error-checking**: Validates step names before updating
3. **Incremental**: Updates saved immediately after each step
4. **Observable**: Progress tracking with completion/failure status
5. **Testable**: Consistent API for testing workflow execution
6. **Maintainable**: Clear separation of concerns

## Migration

If you have existing executors that manually edit manifests:

**Before:**
```python
import json

# Manual JSON editing
data = json.loads(manifest_path.read_text())
for step in data['steps']:
    if step['name'] == 'step_name':
        step['output']['status'] = 'ok'
        step['output']['result'] = result_text
manifest_path.write_text(json.dumps(data, indent=2))
```

**After:**
```python
from aidev import WorkflowManifest

manifest = WorkflowManifest(manifest_path)
manifest.mark_step_complete('step_name', result_text)
```

Much simpler! 🎉

## Questions?

See the example file for more details:
- `src/aidev/examples/workflow_manifest_usage.py`
