"""
Tests for utils.py
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from aidev.utils import (
    expand_path,
    ensure_dir,
    load_json,
    save_json,
    load_env,
    save_env,
    expand_env_vars,
    find_binary,
    run_command,
    confirm,
    print_json,
)


def test_expand_path_with_home(tmp_path, monkeypatch):
    """Test expanding paths with ~ """
    monkeypatch.setenv("HOME", str(tmp_path))

    result = expand_path("~/test/file.txt")

    assert result == tmp_path / "test" / "file.txt"


def test_expand_path_with_env_var(tmp_path, monkeypatch):
    """Test expanding paths with environment variables"""
    monkeypatch.setenv("TESTDIR", str(tmp_path))

    result = expand_path("$TESTDIR/file.txt")

    assert result == tmp_path / "file.txt"


def test_ensure_dir_creates_directory(tmp_path):
    """Test ensure_dir creates directory"""
    test_dir = tmp_path / "new" / "nested" / "dir"

    ensure_dir(test_dir)

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_ensure_dir_idempotent(tmp_path):
    """Test ensure_dir is idempotent"""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Should not raise even if exists
    ensure_dir(test_dir)

    assert test_dir.exists()


def test_load_json_success(tmp_path):
    """Test loading valid JSON"""
    json_file = tmp_path / "test.json"
    data = {"key": "value", "number": 42}
    json_file.write_text(json.dumps(data))

    result = load_json(json_file)

    assert result == data


def test_load_json_file_not_exists(tmp_path):
    """Test loading non-existent JSON file"""
    json_file = tmp_path / "nonexistent.json"

    result = load_json(json_file)

    assert result == {}


def test_load_json_with_default(tmp_path):
    """Test loading non-existent JSON with custom default"""
    json_file = tmp_path / "nonexistent.json"

    result = load_json(json_file, default=["default", "value"])

    assert result == ["default", "value"]


def test_load_json_invalid_json(tmp_path):
    """Test loading invalid JSON"""
    json_file = tmp_path / "invalid.json"
    json_file.write_text("not valid json {")

    with patch("aidev.utils.console"):
        result = load_json(json_file)

    assert result == {}


def test_save_json(tmp_path):
    """Test saving JSON"""
    json_file = tmp_path / "output.json"
    data = {"test": "data", "nested": {"value": 123}}

    save_json(json_file, data)

    assert json_file.exists()
    with open(json_file) as f:
        loaded = json.load(f)
    assert loaded == data


def test_save_json_creates_parent_dirs(tmp_path):
    """Test save_json creates parent directories"""
    json_file = tmp_path / "nested" / "deep" / "file.json"

    save_json(json_file, {"data": "test"})

    assert json_file.exists()
    assert json_file.parent.exists()


def test_load_env_empty_file(tmp_path):
    """Test loading empty env file"""
    env_file = tmp_path / ".env"
    env_file.write_text("")

    result = load_env(env_file)

    assert result == {}


def test_load_env_with_values(tmp_path):
    """Test loading env file with values"""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value1\nKEY2=value2\n")

    result = load_env(env_file)

    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_load_env_handles_comments(tmp_path):
    """Test loading env file ignores comments"""
    env_file = tmp_path / ".env"
    env_file.write_text("# Comment\nKEY=value\n")

    result = load_env(env_file)

    assert result == {"KEY": "value"}


def test_load_env_not_exists(tmp_path):
    """Test loading non-existent env file"""
    env_file = tmp_path / ".env"

    result = load_env(env_file)

    assert result == {}


def test_save_env(tmp_path):
    """Test saving env file"""
    env_file = tmp_path / ".env"
    env_data = {"KEY1": "value1", "KEY2": "value2"}

    save_env(env_file, env_data)

    assert env_file.exists()
    loaded = load_env(env_file)
    assert loaded == env_data


def test_expand_env_vars_simple(monkeypatch):
    """Test expanding environment variables"""
    monkeypatch.setenv("TEST_VAR", "test_value")

    result = expand_env_vars("prefix_${TEST_VAR}_suffix", {"TEST_VAR": "test_value"})

    assert result == "prefix_test_value_suffix"


def test_expand_env_vars_multiple(monkeypatch):
    """Test expanding multiple environment variables"""
    env = {"VAR1": "value1", "VAR2": "value2"}

    result = expand_env_vars("${VAR1} and ${VAR2}", env)

    assert result == "value1 and value2"


def test_expand_env_vars_missing_var(monkeypatch):
    """Test expanding with missing variable"""
    result = expand_env_vars("${MISSING_VAR}", {})

    # Should leave unexpanded
    assert "${MISSING_VAR}" in result or result == ""


def test_find_binary_exists(tmp_path, monkeypatch):
    """Test finding an existing binary"""
    # Create a fake binary
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "test_binary"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    # Add to PATH
    monkeypatch.setenv("PATH", str(bin_dir))

    result = find_binary("test_binary")

    assert result is not None
    assert result.name == "test_binary"


def test_find_binary_not_exists():
    """Test finding non-existent binary"""
    result = find_binary("definitely_not_a_real_binary_12345")

    assert result is None


def test_expand_env_vars_nested_default(monkeypatch):
    """Supports nested default syntax ${VAR:-${INNER:-fallback}}"""
    result = expand_env_vars("${OUTER:-${INNER:-fallback}}", {})
    assert result == "fallback"


def test_run_command_uses_env_and_handles_success(monkeypatch):
    """run_command should merge env and return stdout"""
    called = {}

    class DummyResult:
        def __init__(self):
            self.returncode = 0
            self.stdout = "ok"
            self.stderr = ""

    def fake_run(cmd, cwd=None, env=None, capture_output=True, text=True):
        called["env"] = env
        return DummyResult()

    monkeypatch.setattr("aidev.utils.subprocess.run", fake_run)
    code, out, err = run_command(["echo", "hi"], env={"EXTRA": "1"})

    assert code == 0 and out == "ok" and err == ""
    assert called["env"]["EXTRA"] == "1"


def test_run_command_catches_exception(monkeypatch):
    """run_command should gracefully handle subprocess errors"""
    def boom(*args, **kwargs):
        raise ValueError("explode")

    monkeypatch.setattr("aidev.utils.subprocess.run", boom)
    code, out, err = run_command(["bad"])
    assert code == 1 and out == "" and "explode" in err


def test_print_json_renders(monkeypatch):
    """print_json should render formatted output without error"""
    mock_console = MagicMock()
    monkeypatch.setattr("aidev.utils.console", mock_console)

    print_json({"a": 1}, title="T")

    mock_console.print.assert_called()


# TODO: Fix platform-specific command tests
# def test_run_command_success():
#     """Test running successful command"""
#     returncode, stdout, stderr = run_command("python3 -c 'print(\"test\")'")
#
#     assert returncode == 0
#     assert "test" in stdout
#
#
# def test_run_command_failure():
#     """Test running failed command"""
#     returncode, stdout, stderr = run_command("python3 -c 'import sys; sys.exit(1)'")
#
#     assert returncode != 0
#
#
# def test_run_command_with_output():
#     """Test command output capture"""
#     returncode, stdout, stderr = run_command("python3 -c 'print(\"hello world\")'")
#
#     assert returncode == 0
#     assert "hello world" in stdout


def test_confirm_yes():
    """Test confirm with yes input"""
    with patch("builtins.input", return_value="y"):
        result = confirm("Proceed?")

    assert result is True


def test_confirm_no():
    """Test confirm with no input"""
    with patch("builtins.input", return_value="n"):
        result = confirm("Proceed?")

    assert result is False


def test_confirm_default_true():
    """Test confirm with default True"""
    with patch("builtins.input", return_value=""):
        result = confirm("Proceed?", default=True)

    assert result is True


def test_confirm_default_false():
    """Test confirm with default False"""
    with patch("builtins.input", return_value=""):
        result = confirm("Proceed?", default=False)

    assert result is False


# mask_secret function doesn't exist in utils.py
# These tests are removed
