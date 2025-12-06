"""
Centralized error handling and preflight checks with actionable guidance.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from rich.console import Console

console = Console()


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str
    hint: Optional[str] = None


def check_env(keys: Iterable[str], env_lookup: Callable[[str], Optional[str]]) -> list[CheckResult]:
    """Validate required environment variables exist."""
    results: list[CheckResult] = []
    for key in keys:
        val = env_lookup(key)
        if val:
            results.append(CheckResult(name=key, ok=True, message="set"))
        else:
            results.append(
                CheckResult(
                    name=key,
                    ok=False,
                    message="missing",
                    hint=f"Run: ai env set {key} <value>",
                )
            )
    return results


def check_binaries(binaries: Iterable[str]) -> list[CheckResult]:
    """Validate required binaries are available."""
    results: list[CheckResult] = []
    for bin_name in binaries:
        path = shutil.which(bin_name)
        if path:
            results.append(CheckResult(name=bin_name, ok=True, message=path))
        else:
            results.append(
                CheckResult(
                    name=bin_name,
                    ok=False,
                    message="not found on PATH",
                    hint=f"Install {bin_name} or add it to PATH",
                )
            )
    return results


def render_results(title: str, results: list[CheckResult]) -> bool:
    """Render check results and return True if all passed."""
    if not results:
        console.print(f"[yellow]{title}: no checks defined[/yellow]")
        return True

    passed = True
    for res in results:
        if res.ok:
            console.print(f"[green]✓[/green] {res.name}: {res.message}")
        else:
            passed = False
            hint = f" ({res.hint})" if res.hint else ""
            console.print(f"[red]✗[/red] {res.name}: {res.message}{hint}")
    return passed


def preflight(env_keys: Iterable[str], binaries: Iterable[str], env_lookup: Callable[[str], Optional[str]]) -> bool:
    """Run env and binary checks."""
    ok_env = render_results("Environment", check_env(env_keys, env_lookup))
    ok_bin = render_results("Binaries", check_binaries(binaries))
    return ok_env and ok_bin
