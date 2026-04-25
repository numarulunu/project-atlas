from atlas_backend.models import ModuleHypothesis, PacketPreview, ScanResult

MAX_INCLUDED_FILES = 40
MAX_EXCLUDED_ROOTS = 24
MAX_EVIDENCE_LINES = 10


def compile_smac_packet(scan: ScanResult, module: ModuleHypothesis, question: str) -> PacketPreview:
    needs_full = module.confidence < 0.70 or module.reachability == "unknown"
    included = module.files[:MAX_INCLUDED_FILES]
    included_set = set(module.files)
    excluded = sorted({_root_name(file.path) for file in scan.files if file.path not in included_set})[:MAX_EXCLUDED_ROOTS]
    evidence = [
        f"- `{item.source_file}:{item.source_line}` confidence={item.confidence}: {item.quote}"
        for item in module.evidence[:MAX_EVIDENCE_LINES]
    ]

    markdown = f"""# SMAC Audit Packet

Target module: {module.name}
Plain name: {module.display_name}
Plain meaning: {module.simple_description}
Research question: {question}
Repo: {scan.root_path}
Module confidence: {module.confidence_label} ({round(module.confidence, 2)})
Freshness: {module.freshness}
Safety label: {module.safety_label}
Reachability: {module.reachability}
Needs full SMAC: {str(needs_full).lower()}

## Safety Rules
- Atlas maps are hypotheses, not truth.
- Unknown reachability means no delete.
- No auto-fix, no auto-delete, no auto-reorganize.
- If evidence crosses excluded areas, escalate to full SMAC.

## Allowed read scope
{_bullet(included)}

## Suggested tests
{_bullet(module.tests) if module.tests else "- No mapped tests. Treat this as low safety."}

## Explicit exclusions
{_bullet(excluded)}

## Evidence
{chr(10).join(evidence) if evidence else "- No direct evidence captured for this module yet."}

## Escalate if
- The finding touches files outside allowed read scope.
- The fix would require moving, deleting, or renaming code.
- The module confidence is below 0.70.
- The agent needs unscanned runtime or external reachability evidence.
"""
    return PacketPreview(
        markdown=markdown,
        data={
            "repo": scan.root_path,
            "module": module.name,
            "module_display_name": module.display_name,
            "question": question,
            "confidence": round(module.confidence, 2),
            "confidence_label": module.confidence_label,
            "freshness": module.freshness,
            "reachability": module.reachability,
            "safety_label": module.safety_label,
            "included_files": included,
            "excluded_roots": excluded,
            "tests": module.tests,
            "evidence": [item.__dict__ for item in module.evidence[:MAX_EVIDENCE_LINES]],
            "needs_full_smac": needs_full,
            "destructive_actions_allowed": False,
        },
    )


def _bullet(items: list[str]) -> str:
    if not items:
        return "- None mapped yet. Escalate before assuming this is safe."
    return "\n".join(f"- `{item}`" for item in items)


def _root_name(path: str) -> str:
    return path.split("/", 1)[0]