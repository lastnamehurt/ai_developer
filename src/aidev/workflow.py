"""
Workflow engine and assistant resolver for ai_developer.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from aidev.constants import (
    PROJECT_CONFIG_DIR,
    PROJECT_WORKFLOWS_FILE,
    PROJECT_WORKFLOW_RUNS_DIR,
    WORKFLOWS_TEMPLATE,
)
from aidev.tools import ToolManager
from aidev.utils import console, ensure_dir


@dataclass
class WorkflowStep:
    """Represents a single workflow step."""

    name: str
    profile: str
    prompt: str
    uses_issue_mcp: bool = False


@dataclass
class WorkflowSpec:
    """Workflow definition loaded from YAML."""

    name: str
    description: str
    input_kind: str = "text"
    allow_file: bool = False
    steps: list[WorkflowStep] = field(default_factory=list)


class AssistantResolver:
    """
    Resolve which assistant/tool to use for a workflow step.

    Precedence:
        1) CLI override
        2) Workflow declaration (tool_name if present)
        3) Env var AIDEV_DEFAULT_ASSISTANT
        4) Project config default_assistant
        5) Global default assistant (env)
        6) Hard default ("claude")
        7) Availability fallback: claude -> codex -> cursor -> gemini -> ollama
    """

    FALLBACK_ORDER = ["claude", "codex", "cursor", "gemini", "ollama"]

    def __init__(self, tool_manager: Optional[ToolManager] = None) -> None:
        self.tool_manager = tool_manager or ToolManager()

    def resolve(
        self,
        *,
        cli_override: Optional[str],
        workflow_tool: Optional[str],
        env_default: Optional[str],
        project_default: Optional[str],
    ) -> str:
        """Determine best assistant/tool."""
        for candidate in [
            cli_override,
            workflow_tool,
            env_default,
            project_default,
            "claude",
        ]:
            if candidate:
                return candidate

        return self._fallback_by_availability()

    def _fallback_by_availability(self) -> str:
        """Pick first installed tool in fallback order; default to claude."""
        for candidate in self.FALLBACK_ORDER:
            info = self.tool_manager.detect_tool(candidate)
            if info.installed:
                return candidate
        return "claude"


def detect_ticket_source(ticket_arg: Optional[str], file_arg: Optional[Path]) -> str:
    """
    Infer ticket source type.

    Rules:
      - Jira: ABC-123 pattern or Atlassian URL
      - GitHub: github.com URL or owner/repo#123
      - File: file flag provided
      - Raw: fallback
    """
    if file_arg:
        return "file"
    if ticket_arg:
        if re.search(r"[A-Z]+-\d+", ticket_arg):
            return "jira"
        if "atlassian.net" in ticket_arg:
            return "jira"
        if "github.com" in ticket_arg or re.match(r"[^/]+/[^#]+#\d+", ticket_arg):
            return "github"
        return "raw"
    return "raw"


class WorkflowEngine:
    """Load and execute workflows."""

    def __init__(self, project_dir: Optional[Path] = None) -> None:
        self.project_dir = Path(project_dir or Path.cwd())
        self.tool_manager = ToolManager()
        self.resolver = AssistantResolver(self.tool_manager)

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def workflows_path(self) -> Path:
        """Resolve workflows.yaml path (project-local)."""
        return self.project_dir / PROJECT_CONFIG_DIR / PROJECT_WORKFLOWS_FILE

    def runs_dir(self) -> Path:
        """Directory to store workflow run artifacts."""
        return self.project_dir / PROJECT_CONFIG_DIR / PROJECT_WORKFLOW_RUNS_DIR

    def ensure_workflows_file(self) -> Path:
        """Create project workflows.yaml from template if missing."""
        target = self.workflows_path()
        if target.exists():
            return target
        ensure_dir(target.parent)
        try:
            target.write_text(WORKFLOWS_TEMPLATE.read_text())
            console.print(f"[green]✓[/green] Seeded workflows file at {target}")
        except Exception as exc:  # pragma: no cover - defensive
            console.print(f"[yellow]![/yellow] Could not seed workflows: {exc}")
        return target

    def load_workflows(self) -> dict[str, WorkflowSpec]:
        """Load workflows from YAML (project-local with template fallback)."""
        path = self.ensure_workflows_file()
        data = yaml.safe_load(path.read_text()) or {}
        workflows: dict[str, WorkflowSpec] = {}
        for name, spec in (data.get("workflows") or {}).items():
            steps = [
                WorkflowStep(
                    name=s.get("name"),
                    profile=s.get("profile"),
                    prompt=s.get("prompt"),
                    uses_issue_mcp=bool(s.get("uses_issue_mcp", False)),
                )
                for s in spec.get("steps", [])
            ]
            workflows[name] = WorkflowSpec(
                name=name,
                description=spec.get("description", ""),
                input_kind=spec.get("input", {}).get("kind", "text"),
                allow_file=bool(spec.get("input", {}).get("allow_file", False)),
                steps=steps,
            )
        return workflows

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    def run_workflow(
        self,
        workflow: WorkflowSpec,
        *,
        ticket: Optional[str],
        ticket_file: Optional[Path],
        tool_override: Optional[str],
        project_default_assistant: Optional[str] = None,
    ) -> Path:
        """
        Execute a workflow (lightweight stub): resolve assistants, assemble prompts,
        and persist a run manifest for downstream consumption.
        """
        ticket_source = detect_ticket_source(ticket, ticket_file)
        ticket_text = self._load_ticket_text(ticket, ticket_file)
        steps_output: list[dict[str, Any]] = []

        for step in workflow.steps:
            assistant = self.resolver.resolve(
                cli_override=tool_override,
                workflow_tool=None,
                env_default=self._env_default_assistant(),
                project_default=project_default_assistant,
            )
            prompt_text = self._load_prompt(step.prompt)
            steps_output.append(
                {
                    "name": step.name,
                    "profile": step.profile,
                    "prompt_id": step.prompt,
                    "prompt_text": prompt_text,
                    "assistant": assistant,
                    "uses_issue_mcp": step.uses_issue_mcp,
                    "input": {
                        "ticket_source": ticket_source,
                        "ticket_text_preview": ticket_text[:4000] if ticket_text else "",
                    },
                    "output": None,  # placeholder for future agent output
                }
            )

        manifest = {
            "workflow": workflow.name,
            "description": workflow.description,
            "ticket_source": ticket_source,
            "ticket_arg": ticket,
            "ticket_file": str(ticket_file) if ticket_file else None,
            "steps": steps_output,
            "created_at": int(time.time()),
        }

        run_path = self._persist_run(workflow.name, manifest)
        console.print(f"[green]✓[/green] Workflow '{workflow.name}' prepared. Run manifest: {run_path}")
        # For refactor_scout, emit a local draft ticket for V1 (no remote post)
        if workflow.name == "refactor_scout":
            self._persist_refactor_stub(ticket_file, ticket_text)
        return run_path

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _load_prompt(self, prompt_id: str) -> str:
        """Load prompt text from bundled prompts directory."""
        prompt_path = Path(__file__).parent / "prompts" / f"{prompt_id}.txt"
        if prompt_path.exists():
            return prompt_path.read_text()
        return f"[prompt {prompt_id} not found]"

    def _persist_run(self, workflow_name: str, manifest: dict[str, Any]) -> Path:
        """Write run manifest to .aidev/workflow-runs/."""
        ensure_dir(self.runs_dir())
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        path = self.runs_dir() / f"{workflow_name}-{timestamp}.json"
        path.write_text(json.dumps(manifest, indent=2))
        return path

    def _load_ticket_text(self, ticket_arg: Optional[str], ticket_file: Optional[Path]) -> str:
        """Return ticket text from file or direct string."""
        if ticket_file:
            return ticket_file.read_text()
        return ticket_arg or ""

    def _env_default_assistant(self) -> Optional[str]:
        return shutil.os.environ.get("AIDEV_DEFAULT_ASSISTANT")

    def _persist_refactor_stub(self, ticket_file: Optional[Path], ticket_text: str) -> None:
        """Write a local ticket draft for refactor_scout workflow."""
        ensure_dir(self.runs_dir())
        ts = time.strftime("%Y%m%d-%H%M%S")
        file_hint = str(ticket_file) if ticket_file else "N/A"
        body = [
            "# Refactor Opportunity",
            f"- File: {file_hint}",
            "- Status: draft (local only, V1)",
            "",
            "## Summary",
            ticket_text[:2000] if ticket_text else "Describe the refactor opportunity here.",
            "",
            "## Next Steps",
            "- Convert to issue/ticket when ready",
            "- Validate tests/impact before posting",
        ]
        stub_path = self.runs_dir() / f"refactor_scout-{ts}-draft.md"
        stub_path.write_text("\n".join(body))
        console.print(f"[cyan]Refactor draft saved to[/cyan] {stub_path}")
