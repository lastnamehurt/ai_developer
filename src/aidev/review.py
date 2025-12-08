"""
Lightweight local code review heuristics.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

REVIEW_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md"}


@dataclass
class ReviewComment:
    file_path: str
    line: int
    severity: str
    message: str


@dataclass
class ReviewConfig:
    provider: str = "heuristic"  # heuristic | external
    command: Optional[list[str]] = None  # for external


def load_review_config(path: Optional[Path] = None) -> ReviewConfig:
    config_path = path or Path.home() / ".aidev" / "review.json"
    if not config_path.exists():
        return ReviewConfig()
    try:
        data = json.loads(config_path.read_text())
        provider = data.get("provider", "heuristic")
        command = data.get("command")
        return ReviewConfig(provider=provider, command=command)
    except Exception:
        return ReviewConfig()


def analyze_content(content: str, file_path: str) -> list[ReviewComment]:
    """Run simple heuristics on a file's content."""
    comments: list[ReviewComment] = []
    for idx, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if "TODO" in line or "FIXME" in line:
            comments.append(
                ReviewComment(file_path=file_path, line=idx, severity="info", message="TODO/FIXME left in code")
            )
        if stripped.startswith("except:"):
            comments.append(
                ReviewComment(file_path=file_path, line=idx, severity="error", message="Bare except; catch specific exception")
            )
        if "pdb.set_trace" in line or "breakpoint(" in line:
            comments.append(
                ReviewComment(file_path=file_path, line=idx, severity="warn", message="Debug breakpoint left in code")
            )
        if "print(" in line and not stripped.startswith("#"):
            comments.append(
                ReviewComment(file_path=file_path, line=idx, severity="info", message="Debug print detected")
            )
        if len(line) > 120:
            comments.append(
                ReviewComment(file_path=file_path, line=idx, severity="info", message="Line longer than 120 characters")
            )
    return comments


def analyze_file(path: Path) -> list[ReviewComment]:
    if not path.exists() or not path.is_file():
        return []
    try:
        content = path.read_text()
    except Exception:
        return []
    return analyze_content(content, str(path))


def review_paths(paths: Iterable[Path]) -> list[ReviewComment]:
    comments: list[ReviewComment] = []
    for path in paths:
        if path.suffix.lower() in REVIEW_EXTENSIONS:
            comments.extend(analyze_file(path))
    return comments


def external_review(paths: list[Path], command: list[str]) -> list[ReviewComment]:
    """
    Invoke an external reviewer (e.g., aider/ollama wrapper) by running a command
    with the file list appended. The command's stdout is surfaced as a single comment.
    """
    if not command:
        return []
    cmd = command + [str(p) for p in paths]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout.strip() or result.stderr.strip()
        if not output:
            output = "External reviewer produced no output."
        severity = "error" if result.returncode != 0 else "info"
        return [ReviewComment(file_path="external", line=1, severity=severity, message=output)]
    except Exception as exc:
        return [ReviewComment(file_path="external", line=1, severity="error", message=str(exc))]


def staged_files() -> list[Path]:
    try:
        output = subprocess.check_output(["git", "diff", "--name-only", "--cached"], text=True)
        return [Path(p.strip()) for p in output.splitlines() if p.strip()]
    except Exception:
        return []


def tracked_files() -> list[Path]:
    try:
        output = subprocess.check_output(["git", "ls-files"], text=True)
        return [Path(p.strip()) for p in output.splitlines() if p.strip()]
    except Exception:
        return []
