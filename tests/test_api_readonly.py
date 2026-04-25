from pathlib import Path

from fastapi.testclient import TestClient

from atlas_backend.api import create_app
from atlas_backend.config import AtlasConfig


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "read-only"}


def test_api_has_no_destructive_routes() -> None:
    route_text = "\n".join(route.path for route in create_app().routes)
    forbidden = ["delete", "move", "rename", "write", "commit", "stage", "format"]
    assert not any(word in route_text.lower() for word in forbidden)


def test_project_folder_endpoint_lists_local_candidates(tmp_path: Path, monkeypatch) -> None:
    projects_root = tmp_path / "projects"
    app_folder = projects_root / "SampleApp"
    app_folder.mkdir(parents=True)
    (app_folder / "README.md").write_text("# Sample App\n", encoding="utf-8")
    data_dir = tmp_path / "atlas-data"
    config = AtlasConfig(
        data_dir=data_dir,
        db_path=data_dir / "atlas.db",
        log_path=data_dir / "_atlas.log",
        projects_root=projects_root,
    )
    monkeypatch.setattr("atlas_backend.api.default_config", lambda: config)

    response = TestClient(create_app()).get("/api/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["home_root"] == str(projects_root)
    assert any(project["name"] == "SampleApp" for project in body["projects"])


def test_scan_requires_explicit_folder_choice() -> None:
    response = TestClient(create_app()).get("/api/repo/scan")
    assert response.status_code == 400
    assert response.json()["detail"] == "Choose a project folder first."


def test_packet_preview_endpoint(sample_repo: Path) -> None:
    response = TestClient(create_app()).post(
        "/api/packet/preview",
        json={"repo_path": str(sample_repo), "module_name": "python-core", "question": "audit engine risk"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["destructive_actions_allowed"] is False
    assert "Target module: python-core" in body["markdown"]


def test_prompt_build_endpoint_returns_trigger_prompt(sample_repo: Path) -> None:
    response = TestClient(create_app()).post(
        "/api/prompt/build",
        json={"repo_path": str(sample_repo), "module_name": "python-core", "mode": "diagnose_bug"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trigger_label"] == "Pull trigger"
    assert body["destructive_actions_allowed"] is False
    assert "$smac" in body["prompt"]
    assert "Main engine" in body["prompt"]
