"""
Workflow engine and assistant resolver for ai_developer.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import shlex
import time
from datetime import datetime
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
from aidev.utils import console, ensure_dir, load_json

PROPOSAL_EXEC_SUFFIX = """

[Mode: proposal then execute]
1) Start with a concise proposal: goal, TODO checklist, risks/assumptions, and any approval needed.
2) Write the proposal as Markdown to the path declared in the run manifest (field: proposal_output).
3) If no approval gate is specified, immediately execute the TODOs now—apply edits/files directly.
4) Narrate actions briefly; do not stop after planning.
5) When done, state what you changed and where to find artifacts (edited file paths and the proposal_output path). If you could not write the file, paste the proposal inline and note the intended path.
"""


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
        # Runner hook for step execution; can be overridden in tests
        self._runner: Callable[[dict[str, Any]], dict[str, Any]] = self._default_runner

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
        """Load workflows from YAML (template + project-local merge) with validation warnings.
        
        Template workflows are always loaded and available globally. Project workflows
        can override or extend template workflows. Project workflows take precedence.
        """
        # Load template workflows first (always available)
        template_data = {}
        if WORKFLOWS_TEMPLATE.exists():
            try:
                template_data = yaml.safe_load(WORKFLOWS_TEMPLATE.read_text()) or {}
            except Exception:
                pass
        
        # Load project workflows (if they exist)
        project_data = {}
        project_path = self.workflows_path()
        if project_path.exists():
            try:
                project_data = yaml.safe_load(project_path.read_text()) or {}
            except Exception:
                pass
        
        # Merge: template first, then project (project overrides template)
        merged_workflows = {}
        merged_workflows.update(template_data.get("workflows", {}))
        merged_workflows.update(project_data.get("workflows", {}))
        
        workflows: dict[str, WorkflowSpec] = {}
        warnings: list[str] = []
        for name, spec in merged_workflows.items():
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
        user_prompt: Optional[str],
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
        user_text = user_prompt or ticket_text
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
            prompt_text = self._load_prompt(step.prompt) + PROPOSAL_EXEC_SUFFIX
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
                        "user_prompt": (user_text or "")[:4000],
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
        - Skips steps already marked ok (resume behavior)
        - Updates status/result and writes manifest
        """
        data = json.loads(manifest_path.read_text())
        steps = data.get("steps", [])
        for step in steps:
            if step.get("output", {}).get("status") == "ok":
                continue
            output = step.get("output") or {}
            output["started_at"] = int(time.time())
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
            output["ended_at"] = int(time.time())
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
        manifest["manifest_path"] = str(path)
        manifest["proposal_output"] = str(path.with_suffix(".proposal.md"))
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

    def handoff_to_assistant(self, manifest_path: Path, assistant: str) -> None:
        """
        Launch assistant CLI with an instruction to execute the manifest interactively.
        This opens the assistant; user can watch/drive the steps.
        """
        instruction = (
            "You are a workflow executor. Read the manifest JSON file and execute the steps sequentially. "
            "Use the system prompt as given and the user prompt/ticket content as input. "
            "Narrate your actions and produce outputs per step."
        )
        user_prompt = f"Read and execute the workflow manifest at: {manifest_path}"
        cmd = self._assistant_command(assistant, instruction, user_prompt, user_prompt, interactive=True)
        if not cmd:
            # Special handling for Cursor (GUI app without CLI mode)
            if assistant == "cursor":
                self._handoff_to_cursor(manifest_path)
                return
            console.print(f"[red]✗[/red] No handoff command available for assistant '{assistant}'. Open the manifest manually: {manifest_path}")
            return
        try:
            env = self._assistant_env(assistant)
            # Run inline in the current terminal (avoid opening new Terminal windows).
            result = subprocess.run(cmd, check=False, env=env)
            if result.returncode != 0:
                console.print(f"[red]✗[/red] Assistant '{assistant}' exited with code {result.returncode}.")
                console.print(f"[yellow]Manifest:[/yellow] {manifest_path}")
                console.print(f"[dim]Command:[/dim] {' '.join(cmd)}")
            else:
                console.print(f"[cyan]Opened assistant '{assistant}' with manifest handoff[/cyan]")
        except Exception as exc:
            console.print(f"[red]✗[/red] Failed to launch assistant '{assistant}': {exc}")
            console.print(f"[yellow]Manifest:[/yellow] {manifest_path}")

    def check_workflow_status(self, manifest_path: Path) -> None:
        """Display the current status of a workflow run."""
        try:
            data = json.loads(manifest_path.read_text())
            workflow_name = data.get("workflow", "unknown")
            workflow_desc = data.get("description", "")
            steps = data.get("steps", [])
            completed_at = data.get("completed_at")
            created_at = data.get("created_at", 0)
            
            console.print(f"\n[bold cyan]Workflow:[/bold cyan] {workflow_name}")
            if workflow_desc:
                console.print(f"[dim]Description:[/dim] {workflow_desc}")
            console.print(f"[dim]Manifest:[/dim] {manifest_path}")
            
            if created_at:
                created_time = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
                console.print(f"[dim]Created:[/dim] {created_time}")
            
            if completed_at:
                completed_time = datetime.fromtimestamp(completed_at).strftime("%Y-%m-%d %H:%M:%S")
                console.print(f"[dim]Completed:[/dim] {completed_time}")
                console.print(f"[bold green]✓ Workflow completed[/bold green]\n")
            else:
                console.print(f"[yellow]⏳ Workflow in progress...[/yellow]\n")
            
            # Show step status
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Step", style="cyan", no_wrap=True)
            table.add_column("Status", style="white")
            table.add_column("Assistant", style="dim")
            
            for step in steps:
                step_name = step.get("name", "unknown")
                step_status = step.get("output", {}).get("status", "not-run")
                assistant = step.get("assistant", "unknown")
                
                if step_status == "ok":
                    status_display = "[green]✓ Complete[/green]"
                elif step_status == "error":
                    status_display = "[red]✗ Error[/red]"
                elif step_status == "not-run":
                    status_display = "[yellow]⏳ Pending[/yellow]"
                else:
                    status_display = f"[dim]{step_status}[/dim]"
                
                table.add_row(step_name, status_display, assistant)
            
            console.print(table)
            
            # Show summary
            completed = sum(1 for s in steps if s.get("output", {}).get("status") == "ok")
            errors = sum(1 for s in steps if s.get("output", {}).get("status") == "error")
            pending = len(steps) - completed - errors
            
            console.print(f"\n[dim]Summary:[/dim] {completed} completed, {errors} errors, {pending} pending")
            
            if errors > 0:
                console.print(f"\n[yellow]⚠ Some steps failed. Check the manifest for details.[/yellow]")
            
        except Exception as exc:
            console.print(f"[red]✗[/red] Failed to read manifest: {exc}")

    def _handoff_to_cursor(self, manifest_path: Path) -> None:
        """Handle workflow handoff for Cursor (GUI app without CLI mode)."""
        tool_manager = ToolManager()
        cursor_info = tool_manager.detect_tool("cursor")
        
        if not cursor_info.installed:
            console.print(f"[red]✗[/red] Cursor is not installed.")
            console.print(f"[yellow]Manifest:[/yellow] {manifest_path}")
            console.print(f"[dim]Install Cursor from:[/dim] https://cursor.sh")
            return
        
        # Build the complete prompt for Cursor
        instruction = (
            "You are a workflow executor. Read the manifest JSON file and execute the steps sequentially. "
            "Use the system prompt as given and the user prompt/ticket content as input. "
            "Narrate your actions and produce outputs per step."
        )
        user_prompt = f"Read and execute the workflow manifest at: {manifest_path}"
        
        # Combine instruction and user prompt for Cursor
        full_prompt = f"{instruction}\n\n{user_prompt}"
        
        # Load manifest to get workflow details
        try:
            manifest_data = json.loads(manifest_path.read_text())
            workflow_name = manifest_data.get("workflow", "workflow")
            workflow_desc = manifest_data.get("description", "")
            steps = manifest_data.get("steps", [])
        except Exception:
            workflow_name = "workflow"
            workflow_desc = ""
            steps = []
        
        # Create a prompt file formatted as a direct instruction to Cursor
        # Format it as a clear, actionable prompt that Cursor can execute
        prompt_file = manifest_path.parent / f"{manifest_path.stem}-cursor-prompt.md"
        prompt_content = f"""{full_prompt}

## Workflow Manifest

The workflow manifest JSON file is located at:
`{manifest_path}`

## Instructions

Read the manifest file and execute the workflow steps sequentially. Each step in the manifest contains:
- `prompt_text`: The system prompt for that step
- `input`: Contains `user_prompt` and/or `ticket_text_preview` with the input data

For each step:
1. Read the step's `prompt_text` and `input` fields
2. Execute the step using the prompt_text as the system instruction and the input as the user content
3. Move to the next step and repeat

Begin by reading the manifest file at the path above.

## Workflow Steps ({len(steps)} total)

{chr(10).join(f"- {s.get('name', 'unknown')}" for s in steps)}
"""
        
        try:
            # Write the prompt file
            prompt_file.write_text(prompt_content)
            
            # Open Cursor with ONLY the prompt file (not the manifest)
            # Cursor will read this file and should execute the prompt
            tool_manager.launch_tool("cursor", args=[str(prompt_file)], wait=False)
            console.print(f"[cyan]✓[/cyan] Opened Cursor with workflow prompt")
            console.print(f"[dim]Prompt file: {prompt_file}[/dim]")
            console.print(f"[dim]Manifest: {manifest_path}[/dim]")
            console.print(f"\n[yellow]💡 Tip:[/yellow] Run [bold]ai workflow status {manifest_path.name}[/bold] to check progress")
        except Exception as exc:
            console.print(f"[red]✗[/red] Failed to launch Cursor: {exc}")
            console.print(f"[yellow]Manifest:[/yellow] {manifest_path}")
            console.print(f"\n[yellow]Copy and paste this prompt into Cursor:[/yellow]")
            console.print(f"\n[bold cyan]{full_prompt}[/bold cyan]\n")

    def _default_runner(self, step: dict[str, Any]) -> dict[str, Any]:
        """
        Default step runner: calls assistant binary with prompt text and captures stdout.
        Minimal, best-effort. Real streaming/structured output can be layered later.
        """
        assistant = step.get("assistant")
        prompt_text = step.get("prompt_text", "")
        input_section = step.get("input", {}) or {}
        input_preview = input_section.get("user_prompt") or input_section.get("ticket_text_preview") or ""
        timeout_sec = int(step.get("tool_timeout_sec", 30))
        merged = f"{prompt_text}\n\nINPUT:\n{input_preview}"

        cmd = self._assistant_command(assistant, prompt_text, input_preview, merged, interactive=False)
        if not cmd:
            raise RuntimeError(f"No runner available for assistant '{assistant}'")

        try:
            env = self._assistant_env(assistant)
            proc = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
                env=env,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"{' '.join(cmd)} -> rc={proc.returncode}, stderr={proc.stderr[:200]}")
            return {
                "assistant": assistant,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "prompt_used": prompt_text[:2000],
            }
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Timeout after {timeout_sec}s: {exc}")

    def _assistant_command(
        self,
        assistant: str,
        prompt_text: str,
        input_preview: str,
        merged: str,
        *,
        interactive: bool = False,
    ) -> Optional[list[str]]:
        """
        Map assistant id to a CLI command for non-interactive execution:
        - claude: claude --system-prompt <prompt> <input>
        - codex:  codex --system-prompt <prompt> <input> (fallback to positional prompt only)
        - gemini: gemini --prompt <merged> (interactive flag when handoff)
        - ollama: ollama run llama3.1 --prompt <merged>
        - cursor: unsupported (returns None)
        """
        def _cmd(bin_name: str, args: list[str]) -> Optional[list[str]]:
            return [bin_name, *args] if shutil.which(bin_name) else None

        if assistant == "claude":
            # Claude: system prompt flag plus user text as positional argument
            return _cmd("claude", ["--system-prompt", prompt_text, input_preview])
        if assistant == "codex":
            # Codex: use simple positional prompt; exec subcommand for headless runs
            if interactive:
                return _cmd("codex", [merged])
            return _cmd("codex", ["exec", merged]) or _cmd("codex", [merged])
        if assistant == "gemini":
            # Gemini: use interactive prompt flag for handoff, else one-shot prompt
            if interactive:
                return _cmd("gemini", ["--prompt-interactive", merged]) or _cmd("gemini", ["--prompt", merged])
            return _cmd("gemini", ["--prompt", merged]) or _cmd("gemini", [merged])
        if assistant == "ollama":
            return _cmd("ollama", ["run", "llama3.1", "--prompt", merged])
        if assistant == "cursor":
            return None
        return None

    def _assistant_env(self, assistant: str) -> Optional[dict[str, str]]:
        """Return env overrides for assistants to keep state inside workspace."""
        if assistant in {"claude", "codex", "gemini"}:
            env = os.environ.copy()
            env["HOME"] = str(self.project_dir)
            return env
        return None
