from atlas_backend.models import ModuleGraph, ModuleHypothesis, PacketPreview, ScanResult

MAX_AI_FILES = 80
MAX_AI_NODES = 80
MAX_AI_LINKS = 120
MAX_AI_EVIDENCE = 80


def build_ai_map_review_prompt(scan: ScanResult, modules: list[ModuleHypothesis], graph: ModuleGraph) -> PacketPreview:
    files = [f"{item.path} ({item.language})" for item in scan.files[:MAX_AI_FILES]]
    module_lines = [
        f"{module.name}: {module.display_name} - {module.simple_description}; files={len(module.files)}; tests={len(module.tests)}; safety={module.safety_label}"
        for module in modules
    ]
    node_lines = [
        f"{node.id}: {node.label}; kind={node.kind}; layer={node.layer}; module={node.module_id or 'unknown'}; files={', '.join(node.files[:3])}"
        for node in graph.nodes[:MAX_AI_NODES]
    ]
    link_lines = [
        f"{link.source} -> {link.target}; label={link.label}; kind={link.kind}; layer={link.layer}; files={', '.join(link.files[:3])}"
        for link in graph.links[:MAX_AI_LINKS]
    ]
    evidence_lines = [
        f"{item.kind}: {item.subject} in {item.source_file}:{item.source_line or '?'}"
        for item in scan.evidence[:MAX_AI_EVIDENCE]
    ]

    prompt = f"""$mastermind

Project Atlas map review

Mission:
Improve this codebase map before I aim SMAC. Use only the facts listed below. Do not invent files, modules, tools, or links.

What I need in plain English:
1. Better names for confusing app parts.
2. Missing or wrong links that Atlas should fix.
3. Which nodes should be grouped together.
4. Which areas are uncertain and need big-team SMAC.
5. A short sniper recommendation: where to aim first if something breaks.

Hard safety rules:
- This is read-only analysis.
- Do not suggest deleting, moving, or renaming code.
- If a conclusion is not supported by the facts, mark it as a guess.
- If you need source code content, ask for it instead of pretending.

Project folder:
{scan.root_path}

Mapped app parts:
{_bullet(module_lines)}

Detected files:
{_bullet(files)}

Map nodes:
{_bullet(node_lines)}

Map links:
{_bullet(link_lines)}

Detected imports and symbols:
{_bullet(evidence_lines)}

Return this format:
1. Map corrections
2. Better grouping
3. Missing links to verify
4. Uncertain zones
5. Recommended SMAC target
"""
    return PacketPreview(
        markdown=prompt,
        data={
            "prompt": prompt,
            "trigger_label": "Copy AI review prompt",
            "destructive_actions_allowed": False,
            "sends_code_automatically": False,
            "repo": scan.root_path,
            "file_count_included": len(files),
            "node_count_included": len(node_lines),
            "link_count_included": len(link_lines),
        },
    )


def _bullet(items: list[str]) -> str:
    if not items:
        return "- None detected."
    return "\n".join(f"- {item}" for item in items)
