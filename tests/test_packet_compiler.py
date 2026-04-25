from pathlib import Path

from atlas_backend.module_infer import infer_modules
from atlas_backend.packet import compile_smac_packet
from atlas_backend.scanner import scan_repo


def test_compile_packet_contains_scope_and_exclusions(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.name == "python-core")
    packet = compile_smac_packet(scan, module, "audit engine risk")
    assert "Target module: python-core" in packet.markdown
    assert "Allowed read scope" in packet.markdown
    assert "Explicit exclusions" in packet.markdown
    assert "app/core/engine.py" in packet.markdown


def test_unknown_reachability_forces_no_delete_rule(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.reachability == "unknown")
    packet = compile_smac_packet(scan, module, "find stale leftovers")
    assert "Unknown reachability means no delete" in packet.markdown
    assert packet.data["destructive_actions_allowed"] is False


def test_low_confidence_needs_full_smac(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    module = next(item for item in infer_modules(scan) if item.name == "docs")
    packet = compile_smac_packet(scan, module, "audit docs risk")
    assert packet.data["needs_full_smac"] is True
