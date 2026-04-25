from dataclasses import dataclass


@dataclass(frozen=True)
class FileRecord:
    path: str
    language: str
    size_bytes: int
    sha256: str
    is_test: bool


@dataclass(frozen=True)
class EvidenceRecord:
    kind: str
    subject: str
    source_file: str
    source_line: int | None
    quote: str
    confidence: float
    freshness: str


@dataclass(frozen=True)
class ScanResult:
    repo_name: str
    root_path: str
    head_commit: str | None
    files: list[FileRecord]
    evidence: list[EvidenceRecord]


@dataclass(frozen=True)
class ModuleHypothesis:
    name: str
    display_name: str
    purpose: str
    simple_description: str
    confidence_label: str
    safety_label: str
    files: list[str]
    tests: list[str]
    confidence: float
    freshness: str
    reachability: str
    evidence: list[EvidenceRecord]


@dataclass(frozen=True)
class PacketPreview:
    markdown: str
    data: dict[str, object]


@dataclass(frozen=True)
class ProjectCandidate:
    name: str
    path: str
    description: str
    looks_like_project: bool