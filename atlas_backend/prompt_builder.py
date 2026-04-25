from atlas_backend.graph import build_module_graph
from atlas_backend.models import ModuleGraphNode, ModuleHypothesis, PacketPreview, ScanResult
from atlas_backend.module_infer import infer_modules

MAX_INCLUDED_FILES = 40
MAX_EXCLUDED_ROOTS = 24
MAX_CONTEXT_ITEMS = 16

MODES = {
    "diagnose_bug": {
        "label": "Diagnose bug",
        "mission": "diagnose bug",
        "goal": "Find the likely root cause inside this app part and give me the smallest safe fix plan.",
    },
    "audit_quality": {
        "label": "Audit quality",
        "mission": "quality audit",
        "goal": "Look for correctness, reliability, and maintainability risks inside this app part.",
    },
    "cleanup_risk": {
        "label": "Cleanup risk",
        "mission": "cleanup risk check",
        "goal": "Find redundant or stale-looking code, but do not delete anything. Mark risky cleanup separately.",
    },
}


def build_sniper_prompt(scan: ScanResult, module: ModuleHypothesis, mode: str) -> PacketPreview:
    mode_data = MODES.get(mode, MODES["diagnose_bug"])
    included = module.files[:MAX_INCLUDED_FILES]
    included_set = set(module.files)
    excluded = sorted({_root_name(file.path) for file in scan.files if file.path not in included_set})[:MAX_EXCLUDED_ROOTS]
    tests = module.tests[:20]
    graph_context = _graph_context(scan, module)
    nearby = graph_context["upstream"] + graph_context["downstream"]

    prompt = f"""$smac

Mission: {mode_data["mission"]}
Target: {module.display_name} ({module.name})
Project folder: {scan.root_path}

Plain meaning:
{module.simple_description}

Goal:
{mode_data["goal"]}

Aim only here first:
{_bullet(included)}

Do not wander here unless the evidence clearly forces it:
{_bullet(excluded)}

Checks to run if a fix is proposed:
{_bullet(tests) if tests else "- No mapped checks. Say that safety is lower and ask before risky edits."}

Detected tools and libraries:
{_bullet(graph_context["tools"])}

Detected routes and commands:
{_bullet(graph_context["pipelines"])}

Detected workflow stations:
{_bullet(graph_context["workflow"])}

Nearby connections:
{_bullet(nearby)}

Hard safety rules:
- Atlas maps are hints, not truth.
- Unknown reachability means no delete.
- Do not delete anything.
- Do not move or rename code unless I explicitly approve it.
- If the problem crosses outside the target, stop and ask to escalate to full SMAC.
- If the small team is not enough, call the big team. Do not pretend the narrow scope is enough.

Output in plain English:
1. What is probably wrong.
2. Where to look first.
3. What not to touch.
4. The smallest safe fix plan.
5. What checks prove the fix worked.
"""
    return PacketPreview(
        markdown=prompt,
        data={
            "prompt": prompt,
            "mode": mode,
            "mode_label": mode_data["label"],
            "trigger_label": "Pull trigger",
            "repo": scan.root_path,
            "module": module.name,
            "module_display_name": module.display_name,
            "included_files": included,
            "excluded_roots": excluded,
            "tests": tests,
            "tools": graph_context["tools"],
            "pipelines": graph_context["pipelines"],
            "workflow": graph_context["workflow"],
            "upstream": graph_context["upstream"],
            "downstream": graph_context["downstream"],
            "destructive_actions_allowed": False,
        },
    )


def _graph_context(scan: ScanResult, module: ModuleHypothesis) -> dict[str, list[str]]:
    modules = infer_modules(scan)
    graph = build_module_graph(scan, modules)
    node_by_id = {node.id: node for node in graph.nodes}
    module_node_ids = {node.id for node in graph.nodes if node.id == module.name or node.module_id == module.name}

    tools = [
        _node_context_line(node)
        for node in graph.nodes
        if node.kind == "tool" and node.module_id == module.name
    ]
    pipelines = [
        _node_context_line(node)
        for node in graph.nodes
        if node.layer == "pipelines" and node.module_id == module.name
    ]
    workflow = [
        _node_context_line(node)
        for node in graph.nodes
        if node.layer == "workflow" and (node.module_id == module.name or node.id == module.name)
    ]
    upstream: list[str] = []
    downstream: list[str] = []

    for link in graph.links:
        source = node_by_id.get(link.source)
        target = node_by_id.get(link.target)
        if not source or not target:
            continue
        source_related = source.id in module_node_ids or source.module_id == module.name
        target_related = target.id in module_node_ids or target.module_id == module.name
        if target_related and not source_related:
            upstream.append(f"Incoming: {source.label} {link.label} {target.label}")
        elif source_related and not target_related:
            downstream.append(f"Outgoing: {source.label} {link.label} {target.label}")

    return {
        "tools": _unique(tools)[:MAX_CONTEXT_ITEMS],
        "pipelines": _unique(pipelines)[:MAX_CONTEXT_ITEMS],
        "workflow": _unique(workflow)[:MAX_CONTEXT_ITEMS],
        "upstream": _unique(upstream)[:MAX_CONTEXT_ITEMS],
        "downstream": _unique(downstream)[:MAX_CONTEXT_ITEMS],
    }


def _node_context_line(node: ModuleGraphNode) -> str:
    source = node.metadata.get("manifest") or node.metadata.get("source") or (node.files[0] if node.files else "")
    detail = node.description if node.description and node.description != node.label else ""
    label = f"{node.label} - {detail}" if detail else node.label
    return f"{label} ({source})" if source else label


def _unique(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _bullet(items: list[str]) -> str:
    if not items:
        return "- None mapped. Ask before assuming the scope is safe."
    return "\n".join(f"- {item}" for item in items)


def _root_name(path: str) -> str:
    return path.split("/", 1)[0]
