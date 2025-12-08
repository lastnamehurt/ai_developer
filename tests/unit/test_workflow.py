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

    workflows = engine.load_workflows()
    assert "implement_ticket" in workflows
    assert "refactor_scout" in workflows

    spec = WorkflowSpec(
        name="demo",
        description="demo workflow",
        steps=[WorkflowStep(name="step1", profile="default", prompt="ticket_understander")],
    )
    run_path = engine.run_workflow(spec, ticket="ABC-1", ticket_file=None, tool_override=None)
    assert run_path.exists()
    data = json.loads(run_path.read_text())
    assert data["workflow"] == "demo"
    assert data["steps"][0]["prompt_id"] == "ticket_understander"


def test_refactor_scout_stub(tmp_path: Path):
    project_dir = tmp_path
    code_file = tmp_path / "example.py"
    code_file.write_text("print('hello')")
    engine = WorkflowEngine(project_dir=project_dir)
    wf = engine.load_workflows()["refactor_scout"]

    engine.run_workflow(wf, ticket=None, ticket_file=code_file, tool_override=None)
    runs = list((tmp_path / ".aidev" / "workflow-runs").glob("refactor_scout-*-draft.md"))
    assert runs, "Expected refactor_scout to write a draft ticket file"
