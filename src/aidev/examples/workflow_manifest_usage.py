"""
Example: Using WorkflowManifest helper to update workflow manifests incrementally.

This demonstrates the recommended pattern for workflow executors to update
the manifest after EACH step completes, rather than batching updates at the end.
"""

from aidev import WorkflowManifest
from pathlib import Path


def execute_workflow_example(manifest_path: str) -> None:
    """Example: Execute a workflow and update manifest after each step."""

    # Initialize the manifest helper
    manifest = WorkflowManifest(manifest_path)

    # Get the steps to execute
    steps = manifest.get_all_steps()
    print(f"Executing workflow with {len(steps)} steps")

    # Process each step
    for step in steps:
        step_name = step["name"]
        print(f"\n▶ Executing step: {step_name}")

        try:
            # Execute the step (pseudo-code - replace with actual execution)
            result = execute_step(step)

            # UPDATE MANIFEST IMMEDIATELY - This is the key!
            # Don't wait until all steps are done
            manifest.mark_step_complete(step_name, result)
            print(f"✓ {step_name} completed")

        except Exception as e:
            # If step fails, mark it as failed
            manifest.mark_step_failed(step_name, f"Error: {e}")
            print(f"✗ {step_name} failed: {e}")
            raise

    # Verify all steps completed
    incomplete = manifest.validate()
    if incomplete:
        raise RuntimeError(f"Some steps were not completed: {incomplete}")

    print("\n✓ All steps completed successfully!")


def batching_example(manifest_path: str) -> None:
    """AVOID THIS: Don't batch all updates at the end."""

    manifest = WorkflowManifest(manifest_path)
    steps = manifest.get_all_steps()

    # ❌ This pattern is not recommended
    updates = {}
    for step in steps:
        # ... execute step ...
        updates[step["name"]] = "result summary"

    # Batching all updates at the end loses incremental tracking
    manifest.batch_update(updates)

    print("⚠ All steps batched - not ideal for tracking progress")


def error_handling_example(manifest_path: str) -> None:
    """Example: Proper error handling with manifest updates."""

    manifest = WorkflowManifest(manifest_path)

    for step in manifest.get_all_steps():
        step_name = step["name"]

        try:
            print(f"Executing {step_name}...")
            result = execute_step(step)
            manifest.mark_step_complete(step_name, result)

        except ValueError as e:
            # Mark step as failed with error details
            manifest.mark_step_failed(
                step_name,
                f"Validation error: {e}"
            )
            # Could continue to next step or raise
            raise

        except Exception as e:
            # Generic error handling
            manifest.mark_step_failed(
                step_name,
                f"Unexpected error: {type(e).__name__}: {e}"
            )
            # Could retry or continue
            raise


def progress_tracking_example(manifest_path: str) -> None:
    """Example: Track progress and show status."""

    manifest = WorkflowManifest(manifest_path)
    total_steps = len(manifest.get_all_steps())

    for i, step in enumerate(manifest.get_all_steps(), 1):
        progress = f"[{i}/{total_steps}]"
        print(f"{progress} Executing {step['name']}...")

        try:
            result = execute_step(step)
            manifest.mark_step_complete(step["name"], result)
            print(f"{progress} ✓ {step['name']} complete")

        except Exception as e:
            manifest.mark_step_failed(step["name"], str(e))
            print(f"{progress} ✗ {step['name']} failed")
            raise

    # Show final status
    print(f"\nCompleted: {len(manifest.get_completed_steps())} steps")
    print(f"Failed: {len(manifest.get_failed_steps())} steps")
    failed = manifest.get_failed_steps()
    if failed:
        print(f"Failed steps: {', '.join(failed)}")


def execute_step(step: dict) -> str:
    """Placeholder for actual step execution."""
    step_name = step["name"]
    # In real usage, this would be:
    # - Run the step's tool/command
    # - Capture output
    # - Return summary
    return f"{step_name} executed successfully"


if __name__ == "__main__":
    # This would be called by a workflow executor
    # Example: python workflow_manifest_usage.py /path/to/manifest.json
    import sys

    if len(sys.argv) > 1:
        manifest_path = sys.argv[1]
        print(f"Using manifest: {manifest_path}")
        try:
            execute_workflow_example(manifest_path)
        except Exception as e:
            print(f"Workflow failed: {e}")
            sys.exit(1)
    else:
        print("Usage: python workflow_manifest_usage.py /path/to/manifest.json")
