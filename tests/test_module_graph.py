from pathlib import Path

from atlas_backend.graph import build_module_graph
from atlas_backend.module_infer import infer_modules
from atlas_backend.scanner import scan_repo


def test_module_graph_contains_plain_nodes(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    node_ids = {node.id for node in graph.nodes}

    assert {"python-core", "frontend", "tests", "docs", "scripts"}.issubset(node_ids)
    assert all(node.label and node.description for node in graph.nodes)
    assert all(0 <= node.x <= 100 and 0 <= node.y <= 100 for node in graph.nodes)


def test_module_graph_links_tests_to_checked_module(sample_repo: Path) -> None:
    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))

    assert any(link.source == "tests" and link.target == "python-core" and link.label == "checks" for link in graph.links)
