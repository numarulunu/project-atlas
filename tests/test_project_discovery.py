from pathlib import Path

from atlas_backend.api import list_project_candidates, project_search_roots


def test_project_search_roots_prefers_local_workspace(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "home"
    configured = tmp_path / "installed-next-to-projects"
    workspace = fake_home / "Desktop" / "Claude"
    projects = fake_home / "Projects"
    desktop = fake_home / "Desktop"
    documents = fake_home / "Documents"
    for folder in [configured, workspace, projects, desktop, documents]:
        folder.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    roots = project_search_roots(configured)

    assert roots[:2] == [configured, workspace]
    assert projects in roots
    assert desktop in roots
    assert documents in roots
    assert len(roots) == len({str(root.resolve()) for root in roots})


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
