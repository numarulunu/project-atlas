from pathlib import Path

from atlas_backend.module_infer import infer_modules
from atlas_backend.scanner import scan_repo


def test_infer_sample_repo_core_modules(sample_repo: Path) -> None:
    names = {module.name for module in infer_modules(scan_repo(sample_repo))}
    assert {"python-core", "frontend", "tests"}.issubset(names)


def test_modules_include_confidence_and_reachability(sample_repo: Path) -> None:
    module = next(item for item in infer_modules(scan_repo(sample_repo)) if item.name == "python-core")
    assert 0.0 <= module.confidence <= 1.0
    assert module.reachability in {"known", "unknown", "external"}
    assert module.freshness == "fresh"


def test_unknown_reachability_is_explicit(sample_repo: Path) -> None:
    assert any(module.reachability == "unknown" for module in infer_modules(scan_repo(sample_repo)))
