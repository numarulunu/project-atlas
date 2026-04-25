import posixpath
from pathlib import PurePosixPath

from atlas_backend.models import ModuleGraph, ModuleGraphLink, ModuleGraphNode, ModuleHypothesis, ScanResult

NODE_POSITIONS = {
    "frontend": (18, 28),
    "electron": (18, 58),
    "python-core": (46, 42),
    "tests": (74, 28),
    "docs": (74, 58),
    "scripts": (46, 76),
}

IMPORT_LABEL = "uses"
TEST_LABEL = "checks"


def build_module_graph(scan: ScanResult, modules: list[ModuleHypothesis]) -> ModuleGraph:
    nodes = [_node_for_module(module, index) for index, module in enumerate(modules)]
    module_by_file = {file_path: module.name for module in modules for file_path in module.files}
    file_paths = set(module_by_file)
    links: dict[tuple[str, str, str], ModuleGraphLink] = {}

    for module in modules:
        for test_path in module.tests:
            source = module_by_file.get(test_path)
            if source and source != module.name:
                _add_link(links, source, module.name, TEST_LABEL, "Mapped tests check this app part.")

    for evidence in scan.evidence:
        source = module_by_file.get(evidence.source_file)
        if not source or evidence.kind != "import":
            continue
        target_file = _target_file_for_import(evidence.subject, evidence.source_file, file_paths)
        target = module_by_file.get(target_file) if target_file else None
        if target and target != source:
            _add_link(links, source, target, IMPORT_LABEL, "Detected import connects these app parts.")

    return ModuleGraph(nodes=nodes, links=list(links.values()))


def _node_for_module(module: ModuleHypothesis, index: int) -> ModuleGraphNode:
    x, y = NODE_POSITIONS.get(module.name, _fallback_position(index))
    return ModuleGraphNode(
        id=module.name,
        label=module.display_name,
        description=module.simple_description,
        safety_label=module.safety_label,
        x=x,
        y=y,
    )


def _fallback_position(index: int) -> tuple[int, int]:
    column = index % 3
    row = index // 3
    return 18 + column * 28, min(82, 26 + row * 24)


def _add_link(links: dict[tuple[str, str, str], ModuleGraphLink], source: str, target: str, label: str, reason: str) -> None:
    key = (source, target, label)
    if key not in links:
        links[key] = ModuleGraphLink(source=source, target=target, label=label, reason=reason)


def _target_file_for_import(subject: str, source_file: str, file_paths: set[str]) -> str | None:
    import_name = subject.split(":", 1)[0].strip()
    for candidate in _candidate_paths(import_name, source_file):
        if candidate in file_paths:
            return candidate
    return None


def _candidate_paths(import_name: str, source_file: str) -> list[str]:
    if not import_name:
        return []
    if import_name.startswith("."):
        return _relative_import_candidates(import_name, source_file)
    dotted = import_name.replace(".", "/")
    return [
        f"{dotted}.py",
        f"{dotted}/__init__.py",
        f"{dotted}.js",
        f"{dotted}.jsx",
        f"{dotted}.ts",
        f"{dotted}.tsx",
    ]


def _relative_import_candidates(import_name: str, source_file: str) -> list[str]:
    base = PurePosixPath(source_file).parent.as_posix()
    normalized = posixpath.normpath(posixpath.join(base, import_name))
    suffix = PurePosixPath(normalized).suffix
    if suffix:
        return [normalized]
    return [
        f"{normalized}.js",
        f"{normalized}.jsx",
        f"{normalized}.ts",
        f"{normalized}.tsx",
        f"{normalized}/index.js",
        f"{normalized}/index.jsx",
        f"{normalized}/index.ts",
        f"{normalized}/index.tsx",
    ]
