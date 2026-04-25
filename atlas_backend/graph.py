import json
import posixpath
import re
import tomllib
from pathlib import Path, PurePosixPath

from atlas_backend.models import ModuleGraph, ModuleGraphLink, ModuleGraphNode, ModuleHypothesis, ScanResult

NODE_POSITIONS = {
    "frontend": (18, 28),
    "electron": (18, 58),
    "python-core": (46, 42),
    "tests": (74, 28),
    "docs": (74, 58),
    "scripts": (46, 76),
}
LAYER_ORDER = {
    "overview": 0,
    "pipelines": 1,
    "tools": 2,
    "files": 3,
    "risk": 4,
}
IMPORT_LABEL = "uses"
TEST_LABEL = "checks"
ROUTE_RE = re.compile(r"@(?:\w+\.)?(?P<method>get|post|put|patch|delete)\(['\"](?P<path>[^'\"]+)['\"]")
REQUIREMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+")
MAX_FILE_NODES = 500


def build_module_graph(scan: ScanResult, modules: list[ModuleHypothesis]) -> ModuleGraph:
    root = Path(scan.root_path)
    module_by_file = {file_path: module.name for module in modules for file_path in module.files}
    module_by_name = {module.name: module for module in modules}
    file_paths = set(module_by_file)
    nodes: dict[str, ModuleGraphNode] = {}
    links: dict[tuple[str, str, str], ModuleGraphLink] = {}

    for index, module in enumerate(modules):
        _add_node(nodes, _module_node(module, index))

    for index, file in enumerate(scan.files[:MAX_FILE_NODES]):
        module_id = module_by_file.get(file.path)
        module = module_by_name.get(module_id or "")
        _add_node(nodes, _file_node(file.path, file.language, module, index))

    _add_manifest_nodes(root, scan, nodes, links, module_by_file)
    _add_route_nodes(root, scan, nodes, links, module_by_file)
    _add_import_links(scan, nodes, links, module_by_file, file_paths)
    _add_test_links(modules, links, module_by_file)
    _add_risk_nodes(modules, nodes, links)

    ordered_nodes = sorted(nodes.values(), key=lambda node: (LAYER_ORDER.get(node.layer, 9), node.y, node.x, node.id))
    ordered_links = sorted(links.values(), key=lambda link: (LAYER_ORDER.get(link.layer, 9), link.source, link.target, link.label))
    return ModuleGraph(nodes=ordered_nodes, links=ordered_links)


def _module_node(module: ModuleHypothesis, index: int) -> ModuleGraphNode:
    x, y = NODE_POSITIONS.get(module.name, _fallback_position(index))
    return ModuleGraphNode(
        id=module.name,
        label=module.display_name,
        description=module.simple_description,
        safety_label=module.safety_label,
        x=x,
        y=y,
        kind="module",
        layer="overview",
        module_id=module.name,
        files=module.files,
        metadata={"technical_name": module.name, "confidence": str(module.confidence)},
    )


def _file_node(path: str, language: str, module: ModuleHypothesis | None, index: int) -> ModuleGraphNode:
    x, y = _layer_position("files", index)
    return ModuleGraphNode(
        id=f"file:{path}",
        label=PurePosixPath(path).name,
        description=_file_description(path, language),
        safety_label=module.safety_label if module else "Needs review",
        x=x,
        y=y,
        kind="file",
        layer="files",
        module_id=module.name if module else None,
        files=[path],
        metadata={"path": path, "language": language},
    )


def _file_description(path: str, language: str) -> str:
    if path.startswith("tests/") or "/tests/" in path:
        return "Test file that checks project behavior."
    if path.endswith(("package.json", "pyproject.toml", "requirements.txt")):
        return "Tool and dependency manifest."
    if "component" in path.lower() or path.endswith((".jsx", ".tsx")):
        return "Screen or UI component file."
    if "api" in path.lower() or "route" in path.lower():
        return "API or route file."
    if path.startswith("scripts/"):
        return "Helper script or automation file."
    return f"{language.title()} source file."


def _add_manifest_nodes(
    root: Path,
    scan: ScanResult,
    nodes: dict[str, ModuleGraphNode],
    links: dict[tuple[str, str, str], ModuleGraphLink],
    module_by_file: dict[str, str],
) -> None:
    manifest_files = {file.path for file in scan.files if PurePosixPath(file.path).name in {"package.json", "pyproject.toml", "requirements.txt"}}
    tool_index = 0
    pipeline_index = 0
    for manifest in sorted(manifest_files):
        path = root / manifest
        if not path.exists():
            continue
        module_id = _manifest_module(manifest, module_by_file)
        if manifest.endswith("package.json"):
            tool_index, pipeline_index = _add_package_json(path, manifest, module_id, nodes, links, tool_index, pipeline_index)
        elif manifest.endswith("pyproject.toml"):
            tool_index, pipeline_index = _add_pyproject(path, manifest, module_id, nodes, links, tool_index, pipeline_index, module_by_file)
        elif manifest.endswith("requirements.txt"):
            tool_index = _add_requirements(path, manifest, module_id, nodes, tool_index)


def _add_package_json(
    path: Path,
    manifest: str,
    module_id: str,
    nodes: dict[str, ModuleGraphNode],
    links: dict[tuple[str, str, str], ModuleGraphLink],
    tool_index: int,
    pipeline_index: int,
) -> tuple[int, int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return tool_index, pipeline_index

    dependency_names: set[str] = set()
    for section in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
        values = data.get(section)
        if isinstance(values, dict):
            dependency_names.update(str(name) for name in values)
    for name in sorted(dependency_names):
        _add_node(nodes, _tool_node(f"tool:npm:{name}", name, "npm dependency", module_id, manifest, tool_index))
        tool_index += 1

    scripts = data.get("scripts")
    if isinstance(scripts, dict):
        for name, command in sorted(scripts.items()):
            node_id = f"pipeline:npm:{name}"
            _add_node(nodes, _pipeline_node(node_id, f"npm run {name}", str(command), module_id, manifest, pipeline_index, "script"))
            pipeline_index += 1
            command_tool = _first_command_tool(str(command))
            if command_tool:
                tool_id = f"tool:npm:{command_tool}"
                if tool_id not in nodes:
                    _add_node(nodes, _tool_node(tool_id, command_tool, "npm command used by script", module_id, manifest, tool_index))
                    tool_index += 1
                _add_link(links, node_id, tool_id, "runs", "Script runs this tool.", "script", "pipelines", [manifest])
    return tool_index, pipeline_index


def _add_pyproject(
    path: Path,
    manifest: str,
    module_id: str,
    nodes: dict[str, ModuleGraphNode],
    links: dict[tuple[str, str, str], ModuleGraphLink],
    tool_index: int,
    pipeline_index: int,
    module_by_file: dict[str, str],
) -> tuple[int, int]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return tool_index, pipeline_index

    project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
    dependencies = project.get("dependencies", [])
    if isinstance(dependencies, list):
        for dependency in dependencies:
            name = _requirement_name(str(dependency))
            if not name:
                continue
            _add_node(nodes, _tool_node(f"tool:python:{name}", name, "Python dependency", module_id, manifest, tool_index))
            tool_index += 1

    scripts = project.get("scripts", {})
    if isinstance(scripts, dict):
        for name, target in sorted(scripts.items()):
            node_id = f"pipeline:python:{name}"
            _add_node(nodes, _pipeline_node(node_id, name, str(target), module_id, manifest, pipeline_index, "entrypoint"))
            pipeline_index += 1
            target_file = _target_file_for_entrypoint(str(target), set(module_by_file))
            if target_file:
                _add_link(links, node_id, f"file:{target_file}", "starts", "Entry point starts in this file.", "entrypoint", "pipelines", [manifest, target_file])
    return tool_index, pipeline_index


def _add_requirements(path: Path, manifest: str, module_id: str, nodes: dict[str, ModuleGraphNode], tool_index: int) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return tool_index
    for line in lines:
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        name = _requirement_name(clean)
        if name:
            _add_node(nodes, _tool_node(f"tool:python:{name}", name, "Python dependency", module_id, manifest, tool_index))
            tool_index += 1
    return tool_index


def _add_route_nodes(
    root: Path,
    scan: ScanResult,
    nodes: dict[str, ModuleGraphNode],
    links: dict[tuple[str, str, str], ModuleGraphLink],
    module_by_file: dict[str, str],
) -> None:
    index = 0
    for file in scan.files:
        if file.language != "python":
            continue
        path = root / file.path
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in ROUTE_RE.finditer(text):
            method = match.group("method").upper()
            route_path = match.group("path")
            node_id = f"pipeline:route:{file.path}:{match.group('method')}:{route_path}"
            module_id = module_by_file.get(file.path)
            _add_node(nodes, _pipeline_node(node_id, f"{method} {route_path}", "Backend route", module_id, file.path, index, "route"))
            _add_link(links, node_id, f"file:{file.path}", "handled by", "Route handler lives in this file.", "route", "pipelines", [file.path])
            index += 1


def _add_import_links(
    scan: ScanResult,
    nodes: dict[str, ModuleGraphNode],
    links: dict[tuple[str, str, str], ModuleGraphLink],
    module_by_file: dict[str, str],
    file_paths: set[str],
) -> None:
    tool_index = len([node for node in nodes.values() if node.kind == "tool"])
    for evidence in scan.evidence:
        source_module = module_by_file.get(evidence.source_file)
        source_file_id = f"file:{evidence.source_file}"
        if not source_module or evidence.kind != "import" or source_file_id not in nodes:
            continue
        target_file = _target_file_for_import(evidence.subject, evidence.source_file, file_paths)
        if target_file:
            _add_link(links, source_file_id, f"file:{target_file}", IMPORT_LABEL, "Detected local import connects these files.", "import", "files", [evidence.source_file, target_file])
            target_module = module_by_file.get(target_file)
            if target_module and target_module != source_module:
                _add_link(links, source_module, target_module, IMPORT_LABEL, "Detected import connects these app parts.", "import", "overview", [evidence.source_file, target_file])
            continue
        tool_name = _external_tool_name(evidence.subject)
        if not tool_name:
            continue
        tool_id = f"tool:{_tool_ecosystem(evidence.source_file)}:{tool_name}"
        if tool_id not in nodes:
            _add_node(nodes, _tool_node(tool_id, tool_name, "Imported external library", source_module, evidence.source_file, tool_index))
            tool_index += 1
        _add_link(links, source_file_id, tool_id, "imports", "File imports this external library.", "import", "tools", [evidence.source_file])


def _add_test_links(modules: list[ModuleHypothesis], links: dict[tuple[str, str, str], ModuleGraphLink], module_by_file: dict[str, str]) -> None:
    for module in modules:
        for test_path in module.tests:
            source = module_by_file.get(test_path)
            if source and source != module.name:
                _add_link(links, source, module.name, TEST_LABEL, "Mapped tests check this app part.", "test", "overview", [test_path])
                _add_link(links, f"file:{test_path}", module.name, TEST_LABEL, "Test file checks this app part.", "test", "files", [test_path])


def _add_risk_nodes(modules: list[ModuleHypothesis], nodes: dict[str, ModuleGraphNode], links: dict[tuple[str, str, str], ModuleGraphLink]) -> None:
    index = 0
    for module in modules:
        reasons: list[str] = []
        if module.reachability == "unknown":
            reasons.append("reach is unknown")
        if module.confidence < 0.7:
            reasons.append("map confidence is low")
        if not module.tests and module.name not in {"docs"}:
            reasons.append("no mapped tests")
        if not reasons:
            continue
        x, y = _layer_position("risk", index)
        node_id = f"risk:{module.name}"
        _add_node(
            nodes,
            ModuleGraphNode(
                id=node_id,
                label=f"{module.display_name} needs review",
                description="; ".join(reasons),
                safety_label="Needs big-team check",
                x=x,
                y=y,
                kind="risk",
                layer="risk",
                module_id=module.name,
                files=module.files,
                metadata={"reasons": ", ".join(reasons)},
            ),
        )
        _add_link(links, node_id, module.name, "review", "Risk finding belongs to this module.", "risk", "risk", module.files[:10])
        index += 1


def _tool_node(node_id: str, label: str, description: str, module_id: str | None, manifest: str, index: int) -> ModuleGraphNode:
    x, y = _layer_position("tools", index)
    return ModuleGraphNode(
        id=node_id,
        label=label,
        description=description,
        safety_label="External tool",
        x=x,
        y=y,
        kind="tool",
        layer="tools",
        module_id=module_id,
        files=[manifest],
        metadata={"manifest": manifest},
    )


def _pipeline_node(node_id: str, label: str, description: str, module_id: str | None, path: str, index: int, kind: str) -> ModuleGraphNode:
    x, y = _layer_position("pipelines", index)
    return ModuleGraphNode(
        id=node_id,
        label=label,
        description=description,
        safety_label="Known area" if module_id else "Needs review",
        x=x,
        y=y,
        kind=kind,
        layer="pipelines",
        module_id=module_id,
        files=[path],
        metadata={"source": path},
    )


def _manifest_module(manifest: str, module_by_file: dict[str, str]) -> str:
    if manifest in module_by_file:
        return module_by_file[manifest]
    if manifest.startswith("dashboard/") or manifest.endswith("package.json"):
        return "frontend"
    return "python-core"


def _first_command_tool(command: str) -> str | None:
    first = command.strip().split(maxsplit=1)[0] if command.strip() else ""
    if not first:
        return None
    return first.replace(".cmd", "")


def _requirement_name(requirement: str) -> str | None:
    match = REQUIREMENT_RE.match(requirement.strip())
    return match.group(0).lower().replace("_", "-") if match else None


def _external_tool_name(subject: str) -> str | None:
    import_name = subject.split(":", 1)[0].strip()
    if not import_name or import_name.startswith("."):
        return None
    if import_name.startswith("@"):
        parts = import_name.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else import_name
    return import_name.split(".", 1)[0]


def _tool_ecosystem(source_file: str) -> str:
    return "npm" if source_file.endswith((".js", ".jsx", ".ts", ".tsx")) else "python"


def _target_file_for_entrypoint(target: str, file_paths: set[str]) -> str | None:
    module = target.split(":", 1)[0].strip()
    if not module:
        return None
    return _target_file_for_import(module, "", file_paths)


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


def _add_node(nodes: dict[str, ModuleGraphNode], node: ModuleGraphNode) -> None:
    nodes.setdefault(node.id, node)


def _add_link(
    links: dict[tuple[str, str, str], ModuleGraphLink],
    source: str,
    target: str,
    label: str,
    reason: str,
    kind: str,
    layer: str,
    files: list[str] | None = None,
) -> None:
    if source == target:
        return
    key = (source, target, label)
    if key not in links:
        links[key] = ModuleGraphLink(source=source, target=target, label=label, reason=reason, kind=kind, layer=layer, files=files or [])


def _fallback_position(index: int) -> tuple[int, int]:
    column = index % 3
    row = index // 3
    return 18 + column * 28, min(82, 26 + row * 24)


def _layer_position(layer: str, index: int) -> tuple[int, int]:
    columns = 4 if layer in {"files", "tools"} else 3
    x_start = 14 if columns == 4 else 18
    x_step = 24 if columns == 4 else 28
    y_start = 20
    y_step = 18
    column = index % columns
    row = index // columns
    return x_start + column * x_step, min(86, y_start + row * y_step)
