from pathlib import Path

from atlas_backend.scanner import scan_repo


def test_scan_sample_repo_finds_python_and_frontend_files(sample_repo: Path) -> None:
    result = scan_repo(sample_repo)
    paths = {item.path for item in result.files}
    assert "app/core/engine.py" in paths
    assert "frontend/src/App.jsx" in paths
    assert "tests/core/test_engine.py" in paths


def test_scan_sample_repo_marks_tests(sample_repo: Path) -> None:
    result = scan_repo(sample_repo)
    assert any(item.path.startswith("tests/") and item.is_test for item in result.files)


def test_scan_sample_repo_is_read_only(sample_repo: Path) -> None:
    before = {p.relative_to(sample_repo).as_posix() for p in sample_repo.rglob("*") if p.is_file()}
    scan_repo(sample_repo)
    after = {p.relative_to(sample_repo).as_posix() for p in sample_repo.rglob("*") if p.is_file()}
    assert after == before


def test_scan_skips_stale_file_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    source = repo / "module.py"
    source.write_text("import os\n", encoding="utf-8")

    def stale_evidence(*_args, **_kwargs):
        raise FileNotFoundError("File disappeared during scan")

    monkeypatch.setattr("atlas_backend.scanner._extract_evidence", stale_evidence)
    result = scan_repo(repo)
    assert [item.path for item in result.files] == ["module.py"]
    assert result.evidence == []
