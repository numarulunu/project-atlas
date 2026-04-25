from pathlib import Path

from atlas_backend.graph import build_module_graph
from atlas_backend.module_infer import infer_modules
from atlas_backend.scanner import scan_repo


def test_deep_map_captures_files_tools_routes_scripts_and_risk(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"scripts":{"build":"vite build","test":"vitest run"},"dependencies":{"react":"latest","vite":"latest"}}',
        encoding="utf-8",
    )
    (sample_repo / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.115", "pydantic>=2"]\n[project.scripts]\nsample-api = "app.api:main"\n',
        encoding="utf-8",
    )
    (sample_repo / "app" / "api.py").write_text(
        'from fastapi import FastAPI\nfrom app.core.governor import govern\n\napp = FastAPI()\n\n@app.post("/run")\ndef run_route() -> str:\n    return govern(" ok ")\n\ndef main() -> None:\n    pass\n',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    nodes = {node.id: node for node in graph.nodes}
    links = {(link.source, link.target, link.label) for link in graph.links}

    assert nodes["file:app/api.py"].layer == "files"
    assert nodes["tool:python:fastapi"].layer == "tools"
    assert nodes["tool:npm:react"].layer == "tools"
    assert nodes["pipeline:route:app/api.py:post:/run"].layer == "pipelines"
    assert nodes["pipeline:npm:build"].layer == "pipelines"
    assert nodes["risk:docs"].layer == "risk"
    assert ("file:app/api.py", "file:app/core/governor.py", "uses") in links
    assert ("tests", "python-core", "checks") in links


def test_deep_map_nodes_can_aim_smac_through_module_id(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"dependencies":{"react":"latest"}}',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    nodes = {node.id: node for node in graph.nodes}

    assert nodes["file:app/core/engine.py"].module_id == "python-core"
    assert nodes["tool:npm:react"].module_id == "frontend"
