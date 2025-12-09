import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from aidev.workflow import (
    AssistantResolver,
    WorkflowEngine,
    WorkflowSpec,
    WorkflowStep,
    detect_ticket_source,
)


def test_detect_ticket_source_rules(tmp_path: Path):
    file_path = tmp_path / "ticket.md"
    file_path.write_text("ticket")

    assert detect_ticket_source("ABC-123", None) == "jira"
    assert detect_ticket_source("https://foo.atlassian.net/browse/XYZ-1", None) == "jira"
    assert detect_ticket_source("org/repo#99", None) == "github"
    assert detect_ticket_source("https://github.com/org/repo/issues/9", None) == "github"
    assert detect_ticket_source(None, file_path) == "file"
    assert detect_ticket_source("plain text", None) == "raw"


def test_assistant_resolver_precedence_and_fallback():
    tm = MagicMock()
    tm.detect_tool.return_value.installed = False
    resolver = AssistantResolver(tool_manager=tm)

    assert resolver.resolve(cli_override="codex", workflow_tool=None, env_default=None, project_default=None) == "codex"
    assert resolver.resolve(cli_override=None, workflow_tool="cursor", env_default=None, project_default=None) == "cursor"

    tm.detect_tool.return_value.installed = True
    assert resolver._fallback_by_availability() == "claude"


def test_workflow_engine_seeds_and_runs(tmp_path: Path):
    project_dir = tmp_path
    engine = WorkflowEngine(project_dir=project_dir)
    # Override runner to avoid shelling out during tests
    engine._runner = lambda step: {"assistant": step.get("assistant"), "stdout": "ok"}

    workflows, warnings = engine.load_workflows()
    assert "implement_ticket" in workflows
    assert "refactor_scout" in workflows
    assert warnings == []

    spec = WorkflowSpec(
        name="demo",
        description="demo workflow",
        steps=[WorkflowStep(name="step1", prompt="ticket_understander", tool="claude")],
    )
    run_path = engine.run_workflow(
        spec,
        ticket="ABC-1",
        ticket_file=None,
        user_prompt="hello world",
        tool_override=None,
        from_step=None,
        step_only=False,
    )
    assert run_path.exists()
    data = json.loads(run_path.read_text())
    assert data["workflow"] == "demo"
    assert data["steps"][0]["prompt_id"] == "ticket_understander"
    assert data["schema_version"] == "1.1"
    assert data["steps"][0]["tool_timeout_sec"] == 30
    assert data["steps"][0]["input"]["user_prompt"] == "hello world"
    # Execute placeholder and ensure status/result set
    engine.execute_manifest(run_path)
    executed = json.loads(run_path.read_text())
    assert executed["steps"][0]["output"]["status"] == "ok"


def test_refactor_scout_stub(tmp_path: Path):
    project_dir = tmp_path
    code_file = tmp_path / "example.py"
    code_file.write_text("print('hello')")
    engine = WorkflowEngine(project_dir=project_dir)
    wf = engine.load_workflows()[0]["refactor_scout"]

    engine.run_workflow(
        wf,
        ticket=None,
        ticket_file=code_file,
        user_prompt=None,
        tool_override=None,
        from_step=None,
        step_only=False,
    )
    runs = list((tmp_path / ".aidev" / "workflow-runs").glob("refactor_scout-*-draft.md"))
    assert runs, "Expected refactor_scout to write a draft ticket file"


def test_workflow_spec_minimal_schema():
    """Verify WorkflowSpec works with minimal new schema."""
    spec = WorkflowSpec(
        name="minimal",
        description="Minimal workflow",
        steps=[
            WorkflowStep(name="step1", prompt="prompt1"),
            WorkflowStep(name="step2", prompt="prompt2", tool="claude"),
        ],
    )
    assert spec.name == "minimal"
    assert len(spec.steps) == 2
    assert spec.steps[0].prompt == "prompt1"
    assert spec.steps[1].tool == "claude"
    # Deprecated fields should not exist
    assert not hasattr(spec, "input_kind")
    assert not hasattr(spec, "allow_file")
    assert not hasattr(spec.steps[0], "profile")
    assert not hasattr(spec.steps[0], "uses_issue_mcp")


def test_loader_backward_compatibility(tmp_path):
    """Loader should gracefully ignore old schema fields."""
    old_schema_yaml = """
workflows:
  old_workflow:
    description: "Old schema workflow"
    input:
      kind: ticket
      allow_file: true
    steps:
      - name: step1
        profile: default
        prompt: prompt1
        uses_issue_mcp: true
"""
    workflows_file = tmp_path / "workflows.yaml"
    workflows_file.write_text(old_schema_yaml)

    engine = WorkflowEngine(project_dir=tmp_path)
    # Override workflows path to use our test file
    engine.workflows_path = lambda: workflows_file

    workflows, warnings = engine.load_workflows()
    assert "old_workflow" in workflows
    assert len(warnings) == 0  # Should load without errors

    # Verify minimal fields are present
    wf = workflows["old_workflow"]
    assert wf.description == "Old schema workflow"
    assert len(wf.steps) == 1
    assert wf.steps[0].name == "step1"
    assert wf.steps[0].prompt == "prompt1"


def test_manifest_includes_issue_context(tmp_path):
    """Verify generated manifest includes detected issue context."""
    engine = WorkflowEngine(project_dir=tmp_path)
    engine._runner = lambda step: {"assistant": "claude", "stdout": "ok"}

    spec = WorkflowSpec(
        name="test",
        description="test",
        steps=[WorkflowStep(name="s1", prompt="ticket_understander")],
    )

    run_path = engine.run_workflow(
        spec,
        ticket="ABC-123",
        ticket_file=None,
        user_prompt="Fix ABC-123",
        tool_override=None,
    )

    data = json.loads(run_path.read_text())
    issue_ctx = data["steps"][0]["input"]["issue_context"]
    assert issue_ctx["is_issue"] is True
    assert issue_ctx["issue_type"] == "jira"
    assert issue_ctx["issue_id"] == "ABC-123"
