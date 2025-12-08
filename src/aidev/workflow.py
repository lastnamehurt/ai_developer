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
from typing import Any, Optional, Callable
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
    tool: Optional[str] = None
    timeout_sec: int = 30
    retries: int = 0


@dataclass
class WorkflowSpec:
    """Workflow definition loaded from YAML."""

    name: str
    description: str
    input_kind: str = "text"
    allow_file: bool = False
    steps: list[WorkflowStep] = field(default_factory=list)
    tool_default: Optional[str] = None


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

    def load_workflows(self) -> tuple[dict[str, WorkflowSpec], list[str]]:
        """Load workflows from YAML (project-local with template fallback) with validation warnings."""
        path = self.ensure_workflows_file()
        data = yaml.safe_load(path.read_text()) or {}
        workflows: dict[str, WorkflowSpec] = {}
        warnings: list[str] = []
        for name, spec in (data.get("workflows") or {}).items():
            try:
                steps = []
                for s in spec.get("steps", []):
                    if not s.get("name") or not s.get("profile") or not s.get("prompt"):
                        raise ValueError("step missing name/profile/prompt")
                    steps.append(
                        WorkflowStep(
                            name=s.get("name"),
                            profile=s.get("profile"),
                            prompt=s.get("prompt"),
                            uses_issue_mcp=bool(s.get("uses_issue_mcp", False)),
                            tool=s.get("tool"),
                            timeout_sec=int(s.get("timeout_sec", 30)),
                            retries=int(s.get("retries", 0)),
                        )
                    )

                workflows[name] = WorkflowSpec(
                    name=name,
                    description=spec.get("description", ""),
                    input_kind=spec.get("input", {}).get("kind", "text"),
                    allow_file=bool(spec.get("input", {}).get("allow_file", False)),
                    tool_default=spec.get("tool"),
                    steps=steps,
                )
            except Exception as exc:
                warnings.append(f"{name}: {exc}")
        return workflows, warnings

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
        from_step: Optional[str] = None,
        step_only: bool = False,
    ) -> Path:
        """
        Execute a workflow (lightweight stub): resolve assistants, assemble prompts,
        and persist a run manifest for downstream consumption.
        """
        ticket_source = detect_ticket_source(ticket, ticket_file)
        ticket_text = self._load_ticket_text(ticket, ticket_file)
        steps_output: list[dict[str, Any]] = []

        step_iter = workflow.steps
        if from_step:
            filtered = []
            seen = False
            for step in workflow.steps:
                if step.name == from_step:
                    seen = True
                if seen:
                    filtered.append(step)
            if not seen:
                raise ValueError(f"Step '{from_step}' not found in workflow '{workflow.name}'")
            step_iter = filtered

        for step in step_iter:
            assistant = self.resolver.resolve(
                cli_override=tool_override,
                workflow_tool=step.tool or workflow.tool_default,
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
                    "tool_timeout_sec": step.timeout_sec,
                    "retries": step.retries,
                    "input": {
                        "ticket_source": ticket_source,
                        "ticket_text_preview": ticket_text[:4000] if ticket_text else "",
                    },
                    "output": {
                        "status": "not-run",
                        "result": None,
                    },
                }
            )
            if step_only:
                break

        manifest = {
            "workflow": workflow.name,
            "description": workflow.description,
            "schema_version": "1.1",
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

    def execute_manifest(self, manifest_path: Path) -> Path:
        """
        Execute steps in a manifest:
        - Runs each step via the configured runner (default: assistant CLI best-effort)
        - Respects retries (best-effort)
        - Updates status/result and writes manifest
        """
        data = json.loads(manifest_path.read_text())
        steps = data.get("steps", [])
        for step in steps:
            output = step.get("output") or {}
            retries = step.get("retries", 0)
            attempt = 0
            last_err = None
            while attempt <= retries:
                attempt += 1
                try:
                    result = self._runner(step)
                    output["status"] = "ok"
                    output["result"] = result
                    break
                except Exception as exc:  # pragma: no cover - defensive
                    last_err = str(exc)
                    output["status"] = "error"
                    output["result"] = {"error": last_err, "attempt": attempt}
                    if attempt <= retries:
                        time.sleep(0.1)
            step["output"] = output
        data["completed_at"] = int(time.time())
        manifest_path.write_text(json.dumps(data, indent=2))
        return manifest_path

    # ------------------------------------------------------------------ #
    # Internals / runners
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

    def _default_runner(self, step: dict[str, Any]) -> dict[str, Any]:
        """
        Default step runner: calls assistant binary with prompt text and captures stdout.
        Minimal, best-effort. Real streaming/structured output can be layered later.
        """
        assistant = step.get("assistant")
        prompt_text = step.get("prompt_text", "")
        input_preview = step.get("input", {}).get("ticket_text_preview", "")
        timeout_sec = int(step.get("tool_timeout_sec", 30))

        cmd = self._assistant_command(assistant, prompt_text, input_preview)
        if not cmd:
            raise RuntimeError(f"No runner available for assistant '{assistant}'")

        try:
            proc = shutil.subprocess.run(
                cmd,
                input=input_preview,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
            )
            return {
                "assistant": assistant,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "prompt_used": prompt_text[:2000],
            }
        except shutil.subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Timeout after {timeout_sec}s: {exc}")

    def _assistant_command(self, assistant: str, prompt_text: str, input_preview: str) -> Optional[list[str]]:
        """
        Map assistant id to a CLI command. Minimal, best-effort:
        - claude: `claude chat --message <prompt+input>`
        - codex: `codex chat --message <prompt+input>`
        - gemini: `gemini prompt --text <prompt+input>`
        - cursor: fallback to `echo` (no direct CLI)
        - ollama: `ollama run <model>` with prompt text
        """
        merged = f"{prompt_text}\n\nINPUT:\n{input_preview}"
        if assistant == "claude":
            return ["claude", "chat", "--message", merged]
        if assistant == "codex":
            return ["codex", "chat", "--message", merged]
        if assistant == "gemini":
            return ["gemini", "prompt", "--text", merged]
        if assistant == "ollama":
            return ["ollama", "run", "llama3.1", merged]
        if assistant == "cursor":
            return ["echo", merged]
        return None
