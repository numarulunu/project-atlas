from atlas_backend.models import EvidenceRecord, FileRecord, ModuleHypothesis, ScanResult

CORE_ROOTS = ("backend/", "app/", "server/")
FRONTEND_ROOTS = ("frontend/", "src/", "dashboard/")
ELECTRON_ROOTS = ("electron/",)
SCRIPT_ROOTS = ("scripts/",)
DOC_SUFFIXES = (".md", ".rst")

MODULE_COPY = {
    "python-core": {
        "display_name": "Main engine",
        "purpose": "Core application engine and main backend implementation.",
        "simple_description": "This is the part that does the main work of the app.",
    },
    "frontend": {
        "display_name": "Screen and buttons",
        "purpose": "React user interface.",
        "simple_description": "This is what you see and click on.",
    },
    "electron": {
        "display_name": "Desktop wrapper",
        "purpose": "Desktop shell and IPC.",
        "simple_description": "This is the box that turns the app into a Windows desktop app.",
    },
    "tests": {
        "display_name": "Safety checks",
        "purpose": "Automated verification coverage.",
        "simple_description": "These files check whether the app still works after changes.",
    },
    "docs": {
        "display_name": "Notes and instructions",
        "purpose": "Project documentation and operating notes.",
        "simple_description": "These files explain what the project is and how to use it.",
    },
    "scripts": {
        "display_name": "Helper tools",
        "purpose": "Release, validation, and maintenance helpers.",
        "simple_description": "These are small helper commands used to build, check, or maintain the app.",
    },
}


def infer_modules(scan: ScanResult) -> list[ModuleHypothesis]:
    groups: dict[str, list[FileRecord]] = {
        "python-core": [],
        "frontend": [],
        "electron": [],
        "tests": [],
        "docs": [],
        "scripts": [],
    }
    for file in scan.files:
        if _is_core_path(file.path):
            groups["python-core"].append(file)
        elif _is_frontend_path(file.path):
            groups["frontend"].append(file)
        elif file.path.startswith(ELECTRON_ROOTS):
            groups["electron"].append(file)
        elif file.path.startswith("tests/") or file.is_test:
            groups["tests"].append(file)
        elif file.path.startswith("docs/") or file.path.endswith(DOC_SUFFIXES):
            groups["docs"].append(file)
        elif file.path.startswith(SCRIPT_ROOTS):
            groups["scripts"].append(file)

    return [_make_module(name, files, scan) for name, files in groups.items() if files]


def _make_module(name: str, files: list[FileRecord], scan: ScanResult) -> ModuleHypothesis:
    paths = [file.path for file in files]
    path_set = set(paths)
    tests = [file.path for file in scan.files if _test_targets(file.path, name)]
    evidence = [item for item in scan.evidence if item.source_file in path_set]
    confidence = _confidence(name, paths, tests, evidence)
    copy = MODULE_COPY[name]
    return ModuleHypothesis(
        name=name,
        display_name=copy["display_name"],
        purpose=copy["purpose"],
        simple_description=copy["simple_description"],
        confidence_label=_confidence_label(confidence),
        safety_label=_safety_label(name),
        files=paths,
        tests=tests,
        confidence=confidence,
        freshness="fresh",
        reachability=_reachability(name),
        evidence=evidence[:20],
    )


def _confidence(name: str, paths: list[str], tests: list[str], evidence: list[EvidenceRecord]) -> float:
    score = 0.45
    if paths:
        score += 0.15
    if tests:
        score += 0.15
    if evidence:
        score += 0.15
    if name in {"python-core", "frontend"}:
        score += 0.10
    if name in {"docs", "scripts"}:
        score -= 0.10
    return round(max(0.0, min(score, 0.90)), 2)


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.80:
        return "Strong guess"
    if confidence >= 0.65:
        return "Medium guess"
    return "Weak guess"


def _safety_label(name: str) -> str:
    if _reachability(name) == "known":
        return "Known area"
    return "Needs big-team check"


def _test_targets(path: str, name: str) -> bool:
    if name == "python-core":
        return path.startswith("tests/core/") or path.startswith("tests/cli/")
    if name == "frontend":
        return _is_frontend_path(path) and path.endswith((".test.js", ".test.jsx", ".test.ts", ".test.tsx"))
    if name == "electron":
        return path.startswith("tests/electron/") or (path.startswith("electron/") and ".test." in path)
    if name == "tests":
        return path.startswith("tests/")
    return False


def _reachability(name: str) -> str:
    if name in {"python-core", "frontend", "electron"}:
        return "known"
    return "unknown"


def _is_core_path(path: str) -> bool:
    if path.startswith(("tests/", "scripts/", "docs/")) or path.endswith(DOC_SUFFIXES):
        return False
    return path.startswith(CORE_ROOTS) or path.endswith(".py")


def _is_frontend_path(path: str) -> bool:
    first_part = path.split("/", 1)[0].lower()
    return path.startswith(FRONTEND_ROOTS) or first_part.endswith("frontend")
