"""
Utility functions for aidev
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional
from rich.console import Console
from rich.syntax import Syntax


console = Console()


def expand_path(path: str) -> Path:
    """
    Expand environment variables and user home in path

    Args:
        path: Path with potential variables like $HOME or ~

    Returns:
        Expanded absolute path
    """
    return Path(os.path.expandvars(os.path.expanduser(path)))


def ensure_dir(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any = None) -> Any:
    """
    Load JSON file with error handling

    Args:
        path: Path to JSON file
        default: Default value if file doesn't exist

    Returns:
        Parsed JSON data or default value
    """
    if not path.exists():
        return default if default is not None else {}

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON from {path}: {e}[/red]")
        return default if default is not None else {}


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    """
    Save data as JSON file

    Args:
        path: Path to save JSON file
        data: Data to serialize
        indent: JSON indentation level
    """
    ensure_dir(path.parent)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)


def load_env(path: Path) -> dict[str, str]:
    """
    Load environment variables from .env file

    Args:
        path: Path to .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if not path.exists():
        return env_vars

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                env_vars[key.strip()] = value

    return env_vars


def save_env(path: Path, env_vars: dict[str, str]) -> None:
    """
    Save environment variables to .env file

    Args:
        path: Path to .env file
        env_vars: Dictionary of environment variables
    """
    ensure_dir(path.parent)
    with open(path, "w") as f:
        for key, value in sorted(env_vars.items()):
            f.write(f'{key}="{value}"\n')


def expand_env_vars(text: str, env: dict[str, str]) -> str:
    """
    Expand environment variables in text using custom env dict

    Args:
        text: Text containing ${VAR} or $VAR patterns
        env: Environment variables dictionary

    Returns:
        Text with variables expanded
    """
    result = text
    # First expand ${VAR} syntax
    for key, value in env.items():
        result = result.replace(f"${{{key}}}", value)
        result = result.replace(f"${key}", value)

    # Then expand system env vars
    result = os.path.expandvars(result)
    return result


def find_binary(name: str) -> Optional[Path]:
    """
    Find binary in PATH

    Args:
        name: Binary name to find

    Returns:
        Path to binary if found, None otherwise
    """
    result = shutil.which(name)
    return Path(result) if result else None


def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
    capture: bool = True,
) -> tuple[int, str, str]:
    """
    Run a shell command

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        env: Environment variables
        capture: Whether to capture output

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=process_env,
            capture_output=capture,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def print_json(data: Any, title: Optional[str] = None) -> None:
    """
    Pretty print JSON data with syntax highlighting

    Args:
        data: Data to print
        title: Optional title
    """
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation

    Args:
        message: Confirmation message
        default: Default value if user just presses enter

    Returns:
        True if user confirmed, False otherwise
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = console.input(f"{message}{suffix}").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]
