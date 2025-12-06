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


def test_ollama_review_handles_missing_binary(monkeypatch, tmp_path: Path):
    from aidev import review

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("ollama not found")

    monkeypatch.setattr(review.subprocess, "run", fake_run)
    f = tmp_path / "file.py"
    f.write_text("print('x')")
    comments = review.ollama_review([f], "codellama", "prompt")
    assert comments
    assert comments[0].severity == "error"
    assert "ollama not found" in comments[0].message
