from pathlib import Path

from atlas_backend.api import list_project_candidates


def test_project_candidates_detect_marker_files(tmp_path: Path) -> None:
    app = tmp_path / "FriendApp"
    app.mkdir()
    (app / "package.json").write_text("{}", encoding="utf-8")
    candidates = list_project_candidates([tmp_path])
    assert candidates[0].name == "FriendApp"
    assert candidates[0].looks_like_project is True


def test_project_candidates_ignore_generated_folders(tmp_path: Path) -> None:
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    candidates = list_project_candidates([tmp_path])
    assert all(candidate.name != "node_modules" for candidate in candidates)