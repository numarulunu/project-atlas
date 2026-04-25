from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from atlas_backend.config import default_config
from atlas_backend.logging_config import configure_logging
from atlas_backend.graph import build_module_graph
from atlas_backend.models import ProjectCandidate
from atlas_backend.module_infer import infer_modules
from atlas_backend.packet import compile_smac_packet
from atlas_backend.prompt_builder import build_sniper_prompt
from atlas_backend.scanner import scan_repo

IGNORED_PROJECT_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    "_memory-backup-20260405",
    "_conversations",
    "_minifier_video_test",
}


class PacketPreviewRequest(BaseModel):
    repo_path: str | None = None
    module_name: str
    question: str


class PromptBuildRequest(BaseModel):
    repo_path: str | None = None
    module_name: str
    mode: str = "diagnose_bug"


def create_app() -> FastAPI:
    config = default_config()
    configure_logging(config.log_path)
    app = FastAPI(title="Project Atlas", version="0.4.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "read-only"}

    @app.get("/api/projects")
    def projects() -> dict[str, object]:
        roots = project_search_roots(config.projects_root)
        candidates = list_project_candidates(roots)
        return {
            "home_root": str(roots[0]),
            "home_roots": [str(root) for root in roots],
            "projects": [asdict(candidate) for candidate in candidates],
        }

    @app.get("/api/repo/scan")
    def repo_scan(repo_path: str | None = None) -> dict[str, object]:
        if not repo_path:
            raise HTTPException(status_code=400, detail="Choose a project folder first.")
        scan = scan_repo(Path(repo_path))
        modules = infer_modules(scan)
        return {
            "repo": scan.repo_name,
            "root_path": scan.root_path,
            "head_commit": scan.head_commit,
            "file_count": len(scan.files),
            "modules": [asdict(module) for module in modules],
            "graph": asdict(build_module_graph(scan, modules)),
        }

    @app.post("/api/packet/preview")
    def packet_preview(request: PacketPreviewRequest) -> dict[str, object]:
        if not request.repo_path:
            raise HTTPException(status_code=400, detail="Choose a project folder first.")
        scan = scan_repo(Path(request.repo_path))
        module = _find_module(scan, request.module_name)
        packet = compile_smac_packet(scan, module, request.question)
        return {"markdown": packet.markdown, **packet.data}

    @app.post("/api/prompt/build")
    def prompt_build(request: PromptBuildRequest) -> dict[str, object]:
        if not request.repo_path:
            raise HTTPException(status_code=400, detail="Choose a project folder first.")
        scan = scan_repo(Path(request.repo_path))
        module = _find_module(scan, request.module_name)
        prompt = build_sniper_prompt(scan, module, request.mode)
        return {"markdown": prompt.markdown, **prompt.data}

    return app


def _find_module(scan, module_name: str):
    module = next((item for item in infer_modules(scan) if item.name == module_name), None)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


def project_search_roots(primary_root: Path | None = None) -> list[Path]:
    home = Path.home()
    roots = [root for root in [
        primary_root,
        home / "Desktop" / "Claude",
        home / "Projects",
        home / "Desktop",
        home / "Documents",
    ] if root is not None]
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        expanded = root.expanduser()
        key = str(expanded.resolve()) if expanded.exists() else str(expanded)
        if expanded.exists() and expanded.is_dir() and key not in seen:
            out.append(expanded)
            seen.add(key)
    return out or [home]


def list_project_candidates(roots: Path | Iterable[Path]) -> list[ProjectCandidate]:
    if isinstance(roots, Path):
        root_list = [roots]
    else:
        root_list = list(roots)

    candidates: list[ProjectCandidate] = []
    seen: set[str] = set()
    for root in root_list:
        expanded = root.expanduser()
        if not expanded.exists() or not expanded.is_dir():
            continue
        for child in sorted(expanded.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir() or child.name.startswith(".") or child.name in IGNORED_PROJECT_DIRS:
                continue
            key = str(child.resolve())
            if key in seen:
                continue
            seen.add(key)
            looks_like_project = _looks_like_project(child)
            description = "Looks like an app folder" if looks_like_project else "Folder"
            candidates.append(ProjectCandidate(child.name, str(child), description, looks_like_project))
    return sorted(candidates, key=lambda item: (not item.looks_like_project, item.name.lower()))[:80]


def _looks_like_project(path: Path) -> bool:
    markers = [".git", "pyproject.toml", "package.json", "README.md", "requirements.txt", "Cargo.toml", "go.mod"]
    return any((path / marker).exists() for marker in markers)


app = create_app()
