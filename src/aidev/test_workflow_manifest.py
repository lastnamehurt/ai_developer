"""
Tests for WorkflowManifest helper class.
"""

import json
import tempfile
from pathlib import Path
import pytest

from aidev.workflow import WorkflowManifest


@pytest.fixture
def sample_manifest():
    """Create a sample manifest for testing."""
    return {
        "workflow": "test_workflow",
        "description": "Test workflow",
        "steps": [
            {
                "name": "step_one",
                "output": {"status": "not-run", "result": None},
            },
            {
                "name": "step_two",
                "output": {"status": "not-run", "result": None},
            },
            {
                "name": "step_three",
                "output": {"status": "not-run", "result": None},
            },
        ],
    }


@pytest.fixture
def temp_manifest_file(sample_manifest):
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_manifest, f)
        path = f.name
    yield path
    Path(path).unlink()


def test_mark_step_complete(temp_manifest_file):
    """Test marking a step as complete."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_complete("step_one", "Step one result")

    # Verify the update
    manifest = WorkflowManifest(temp_manifest_file)  # Reload from disk
    assert manifest.get_step("step_one")["output"]["status"] == "ok"
    assert manifest.get_step("step_one")["output"]["result"] == "Step one result"


def test_mark_step_failed(temp_manifest_file):
    """Test marking a step as failed."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_failed("step_one", "Error occurred")

    manifest = WorkflowManifest(temp_manifest_file)
    assert manifest.get_step("step_one")["output"]["status"] == "failed"
    assert manifest.get_step("step_one")["output"]["result"] == "Error occurred"


def test_validate_all_complete(temp_manifest_file):
    """Test validation when all steps are complete."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_complete("step_one", "done")
    manifest.mark_step_complete("step_two", "done")
    manifest.mark_step_complete("step_three", "done")

    incomplete = manifest.validate()
    assert incomplete == []


def test_validate_incomplete_steps(temp_manifest_file):
    """Test validation with incomplete steps."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_complete("step_one", "done")
    # step_two and step_three are not completed

    incomplete = manifest.validate()
    assert set(incomplete) == {"step_two", "step_three"}


def test_get_completed_steps(temp_manifest_file):
    """Test getting completed steps."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_complete("step_one", "done")
    manifest.mark_step_complete("step_three", "done")

    completed = manifest.get_completed_steps()
    assert set(completed) == {"step_one", "step_three"}


def test_get_failed_steps(temp_manifest_file):
    """Test getting failed steps."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.mark_step_complete("step_one", "done")
    manifest.mark_step_failed("step_two", "error")
    manifest.mark_step_failed("step_three", "error")

    failed = manifest.get_failed_steps()
    assert set(failed) == {"step_two", "step_three"}


def test_batch_update(temp_manifest_file):
    """Test batch updating multiple steps."""
    manifest = WorkflowManifest(temp_manifest_file)

    manifest.batch_update(
        {
            "step_one": "result 1",
            "step_two": "result 2",
        }
    )

    manifest = WorkflowManifest(temp_manifest_file)
    assert manifest.get_step("step_one")["output"]["status"] == "ok"
    assert manifest.get_step("step_two")["output"]["status"] == "ok"
    assert manifest.get_step("step_three")["output"]["status"] == "not-run"


def test_get_step_not_found(temp_manifest_file):
    """Test getting a non-existent step."""
    manifest = WorkflowManifest(temp_manifest_file)
    assert manifest.get_step("nonexistent") is None


def test_mark_nonexistent_step_raises(temp_manifest_file):
    """Test that marking a non-existent step raises error."""
    manifest = WorkflowManifest(temp_manifest_file)

    with pytest.raises(ValueError, match="Step 'nonexistent' not found"):
        manifest.mark_step_complete("nonexistent", "result")


def test_manifest_not_found():
    """Test that loading non-existent manifest raises error."""
    with pytest.raises(FileNotFoundError):
        WorkflowManifest("/nonexistent/path/manifest.json")


def test_invalid_json():
    """Test that invalid JSON raises error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json")
        path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            WorkflowManifest(path)
    finally:
        Path(path).unlink()


def test_incremental_updates(temp_manifest_file):
    """Test the recommended pattern: incremental updates after each step."""
    manifest = WorkflowManifest(temp_manifest_file)

    # Simulate executing steps one by one
    for i, step in enumerate(manifest.get_all_steps(), 1):
        result = f"Step {step['name']} completed"
        manifest.mark_step_complete(step["name"], result)

        # Verify each update is saved immediately
        manifest = WorkflowManifest(temp_manifest_file)
        completed = manifest.get_completed_steps()
        assert len(completed) == i
        assert step["name"] in completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
