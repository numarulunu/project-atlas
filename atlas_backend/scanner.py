import ast
import hashlib
import logging
import re
import subprocess
from pathlib import Path

from atlas_backend.models import EvidenceRecord, FileRecord, ScanResult

LOGGER = logging.getLogger(__name__)

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "build",
    "tmp",
    ".venv",
    "venv",
}
LANG_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
}
IMPORT_RE = re.compile(r"(?:^import\s+.+?\s+from\s+['\"](?P<from>[^'\"]+)['\"]|^import\s+['\"](?P<bare>[^'\"]+)['\"]|require\(['\"](?P<require>[^'\"]+)['\"]\))")


def scan_repo(root: Path) -> ScanResult:
    root = root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repo folder not found: {root}")

    LOGGER.info("Scanning repo read-only: %s", root)
    files: list[FileRecord] = []
    evidence: list[EvidenceRecord] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel_path.parts):
            continue
        language = LANG_BY_SUFFIX.get(path.suffix.lower())
        if language is None:
            continue
        rel = rel_path.as_posix()
        try:
            data = path.read_bytes()
        except OSError as exc:
            LOGGER.warning("Skipping stale file during scan: %s (%s)", path, exc)
            continue
        files.append(
            FileRecord(
                path=rel,
                language=language,
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                is_test=_is_test_path(rel),
            )
        )
        try:
            evidence.extend(_extract_evidence(path, root, language))
        except OSError as exc:
            LOGGER.warning("Skipping stale evidence during scan: %s (%s)", path, exc)

    LOGGER.info("Scan complete: %s files, %s evidence records", len(files), len(evidence))
    return ScanResult(root.name, str(root), _git_head(root), files, evidence)


def _git_head(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _is_test_path(path: str) -> bool:
    name = Path(path).name
    return (
        path.startswith("tests/")
        or "/tests/" in path
        or name.startswith("test_")
        or name.endswith((".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.ts"))
    )


def _extract_evidence(path: Path, root: Path, language: str) -> list[EvidenceRecord]:
    if language == "python":
        return _extract_python_evidence(path, root)
    if language in {"javascript", "typescript"}:
        return _extract_js_evidence(path, root)
    return []


def _extract_python_evidence(path: Path, root: Path) -> list[EvidenceRecord]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    evidence: list[EvidenceRecord] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return evidence

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            subject = ", ".join(alias.name for alias in node.names)
            evidence.append(_record("import", subject, rel, node.lineno, lines, 0.9))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            subject = f"{module}: {names}" if module else names
            evidence.append(_record("import", subject, rel, node.lineno, lines, 0.9))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            evidence.append(_record("symbol", node.name, rel, node.lineno, lines, 0.8))
    return evidence


def _extract_js_evidence(path: Path, root: Path) -> list[EvidenceRecord]:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    evidence: list[EvidenceRecord] = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        match = IMPORT_RE.search(stripped)
        if match:
            subject = next(group for group in match.groups() if group)
            evidence.append(_record("import", subject, rel, line_no, lines, 0.78))
    return evidence


def _record(kind: str, subject: str, source_file: str, line_no: int, lines: list[str], confidence: float) -> EvidenceRecord:
    quote = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else subject
    return EvidenceRecord(kind, subject, source_file, line_no, quote, confidence, "fresh")
