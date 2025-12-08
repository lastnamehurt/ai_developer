from pathlib import Path

from aidev.review import analyze_content, review_paths, external_review


def test_analyze_content_detects_bare_except_and_todo():
    content = "try:\n    pass\nexcept:\n    pass  # TODO fix\n"
    comments = analyze_content(content, "sample.py")
    messages = [c.message for c in comments]
    assert any("Bare except" in m for m in messages)
    assert any("TODO" in m for m in messages)


def test_review_paths_filters_extensions(tmp_path: Path):
    py_file = tmp_path / "file.py"
    txt_file = tmp_path / "notes.txt"
    py_file.write_text("print('debug')\n")
    txt_file.write_text("print('ignore')\n")
    comments = review_paths([py_file, txt_file])
    assert any("debug" in c.message.lower() for c in comments)
    assert all(c.file_path.endswith(".py") for c in comments)


def test_external_review_handles_missing_command():
    comments = external_review([], [])
    assert comments == []


def test_analyze_content_detects_debug_breakpoint():
    """Test detection of debug breakpoints"""
    content = "import pdb\npdb.set_trace()\nbreakpoint()\n"
    comments = analyze_content(content, "test.py")
    messages = [c.message for c in comments]
    assert any("breakpoint" in m.lower() for m in messages)
    assert len(comments) >= 2  # Should detect both


def test_analyze_content_detects_long_lines():
    """Test detection of long lines"""
    content = "x = " + "a" * 130 + "\n"
    comments = analyze_content(content, "test.py")
    assert any("120 characters" in c.message for c in comments)


def test_analyze_content_no_issues():
    """Test clean code with no issues"""
    content = "def hello():\n    return 'world'\n"
    comments = analyze_content(content, "test.py")
    assert len(comments) == 0


def test_analyze_file_nonexistent():
    """Test analyzing non-existent file"""
    from aidev.review import analyze_file
    result = analyze_file(Path("/nonexistent/file.py"))
    assert result == []


def test_analyze_file_directory(tmp_path: Path):
    """Test analyzing a directory instead of file"""
    from aidev.review import analyze_file
    result = analyze_file(tmp_path)
    assert result == []


def test_analyze_file_unreadable(tmp_path: Path):
    """Test analyzing unreadable file"""
    from aidev.review import analyze_file
    import os
    file = tmp_path / "test.py"
    file.write_text("print('test')")
    # Make file unreadable
    os.chmod(file, 0o000)
    try:
        result = analyze_file(file)
        assert result == []
    finally:
        # Restore permissions for cleanup
        os.chmod(file, 0o644)


def test_analyze_file_success(tmp_path: Path):
    """Test successful file analysis"""
    from aidev.review import analyze_file
    file = tmp_path / "test.py"
    file.write_text("try:\n    pass\nexcept:\n    pass\n")
    result = analyze_file(file)
    assert len(result) > 0
    assert any("Bare except" in c.message for c in result)


def test_review_paths_empty():
    """Test reviewing empty path list"""
    comments = review_paths([])
    assert comments == []


def test_review_paths_multiple_files(tmp_path: Path):
    """Test reviewing multiple files"""
    file1 = tmp_path / "file1.py"
    file2 = tmp_path / "file2.py"
    file1.write_text("# TODO: fix this\n")
    file2.write_text("except:\n    pass\n")
    
    comments = review_paths([file1, file2])
    assert len(comments) >= 2
    assert any("TODO" in c.message for c in comments)
    assert any("Bare except" in c.message for c in comments)


def test_external_review_success(tmp_path: Path, monkeypatch):
    """Test successful external review"""
    from aidev import review
    import subprocess
    
    class MockResult:
        returncode = 0
        stdout = "Review passed"
        stderr = ""
    
    def mock_run(*args, **kwargs):
        return MockResult()
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    file = tmp_path / "test.py"
    file.write_text("print('test')")
    comments = external_review([file], ["echo", "reviewing"])
    
    assert len(comments) == 1
    assert comments[0].severity == "info"
    assert "Review passed" in comments[0].message


def test_external_review_failure(tmp_path: Path, monkeypatch):
    """Test external review with non-zero exit"""
    from aidev import review
    import subprocess
    
    class MockResult:
        returncode = 1
        stdout = ""
        stderr = "Error occurred"
    
    def mock_run(*args, **kwargs):
        return MockResult()
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    file = tmp_path / "test.py"
    file.write_text("print('test')")
    comments = external_review([file], ["reviewer"])
    
    assert len(comments) == 1
    assert comments[0].severity == "error"


def test_external_review_exception(tmp_path: Path, monkeypatch):
    """Test external review with exception"""
    from aidev import review
    import subprocess
    
    def mock_run(*args, **kwargs):
        raise RuntimeError("Command failed")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    file = tmp_path / "test.py"
    file.write_text("print('test')")
    comments = external_review([file], ["reviewer"])
    
    assert len(comments) == 1
    assert comments[0].severity == "error"
    assert "Command failed" in comments[0].message



def test_load_review_config_default():
    """Test loading default config when file doesn't exist"""
    from aidev.review import load_review_config
    config = load_review_config(Path("/nonexistent/review.json"))
    assert config.provider == "heuristic"
    assert config.command is None
    assert config.ollama_model == "codellama"


def test_load_review_config_custom(tmp_path: Path):
    """Test loading custom config"""
    from aidev.review import load_review_config
    import json
    
    config_file = tmp_path / "review.json"
    config_data = {
        "provider": "external",
        "command": ["aider", "review"],
        "ollama_model": "llama2",
        "ollama_prompt": "Custom prompt"
    }
    config_file.write_text(json.dumps(config_data))
    
    config = load_review_config(config_file)
    assert config.provider == "external"
    assert config.command == ["aider", "review"]
    assert config.ollama_model == "llama2"
    assert config.ollama_prompt == "Custom prompt"


def test_load_review_config_invalid_json(tmp_path: Path):
    """Test loading config with invalid JSON"""
    from aidev.review import load_review_config
    
    config_file = tmp_path / "review.json"
    config_file.write_text("not valid json")
    
    config = load_review_config(config_file)
    assert config.provider == "heuristic"  # Falls back to default
