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
