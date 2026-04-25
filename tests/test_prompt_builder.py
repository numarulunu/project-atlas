from pathlib import Path

from atlas_backend.module_infer import infer_modules
from atlas_backend.prompt_builder import build_sniper_prompt
from atlas_backend.scanner import scan_repo


def test_sniper_prompt_targets_module_with_smac_trigger(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.name == "python-core")
    prompt = build_sniper_prompt(scan, module, "diagnose_bug")
    assert prompt.data["trigger_label"] == "Pull trigger"
    assert prompt.data["destructive_actions_allowed"] is False
    assert "$smac" in prompt.markdown
    assert "Main engine" in prompt.markdown
    assert "app/core/engine.py" in prompt.markdown
    assert "Unknown reachability means no delete" in prompt.markdown


def test_sniper_prompt_changes_mission_by_mode(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.name == "frontend")
    prompt = build_sniper_prompt(scan, module, "cleanup_risk")
    assert "Mission: cleanup risk check" in prompt.markdown
    assert "Do not delete anything" in prompt.markdown


def test_sniper_prompt_includes_tools_pipelines_and_neighbors(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"scripts":{"build":"vite build"},"dependencies":{"react":"latest","vite":"latest"}}',
        encoding="utf-8",
    )
    (sample_repo / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.115"]\n[project.scripts]\nsample-api = "app.core.governor:govern"\n',
        encoding="utf-8",
    )
    (sample_repo / "app" / "api.py").write_text(
        'from fastapi import FastAPI\nfrom app.core.governor import govern\n\napp = FastAPI()\n\n@app.post("/run")\ndef run_route() -> str:\n    return govern(" ok ")\n',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.name == "python-core")
    prompt = build_sniper_prompt(scan, module, "diagnose_bug")

    assert "Detected tools and libraries:" in prompt.markdown
    assert "fastapi" in prompt.markdown
    assert "Detected routes and commands:" in prompt.markdown
    assert "POST /run" in prompt.markdown
    assert "sample-api" in prompt.markdown
    assert "Nearby connections:" in prompt.markdown
    assert prompt.data["tools"]
    assert prompt.data["pipelines"]
