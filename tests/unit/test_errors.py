from aidev.errors import check_env, check_binaries, preflight


def test_check_env_missing_and_set():
    env = {"ONE": "1"}
    results = check_env(["ONE", "TWO"], env.get)
    assert len(results) == 2
    assert results[0].ok
    assert not results[1].ok
    assert "ai env set TWO" in (results[1].hint or "")


def test_check_binaries(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    (tmp_path / "present").write_text("#!/bin/sh\necho ok\n")
    (tmp_path / "present").chmod(0o755)
    results = check_binaries(["present", "missing"])
    assert any(r.ok for r in results if r.name == "present")
    assert any(not r.ok for r in results if r.name == "missing")


def test_preflight_combines(monkeypatch):
    env = {"KEY": "VAL"}
    env_lookup = env.get
    # Force binaries to fail
    monkeypatch.setenv("PATH", "/nonexistent")
    ok = preflight(["KEY"], ["definitely_missing_binary"], env_lookup)
    assert not ok
