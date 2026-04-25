from atlas_backend.models import ModuleHypothesis, PacketPreview, ScanResult

MAX_INCLUDED_FILES = 40
MAX_EXCLUDED_ROOTS = 24

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
            "destructive_actions_allowed": False,
        },
    )


def _bullet(items: list[str]) -> str:
    if not items:
        return "- None mapped. Ask before assuming the scope is safe."
    return "\n".join(f"- {item}" for item in items)


def _root_name(path: str) -> str:
    return path.split("/", 1)[0]