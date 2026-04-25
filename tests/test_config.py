from pathlib import Path

from atlas_backend.config import default_config


def test_default_config_uses_installed_repo_not_private_workspace(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    config = default_config()
    repo_root = Path(__file__).resolve().parents[1]

    assert config.data_dir == repo_root / ".atlas"
    assert config.projects_root == repo_root.parent
