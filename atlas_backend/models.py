from dataclasses import dataclass, field


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
class ModuleGraphNode:
    id: str
    label: str
    description: str
    safety_label: str
    x: int
    y: int
    kind: str = "module"
    layer: str = "overview"
    module_id: str | None = None
    files: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModuleGraphLink:
    source: str
    target: str
    label: str
    reason: str
    kind: str = "relationship"
    layer: str = "overview"
    files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModuleGraph:
    nodes: list[ModuleGraphNode]
    links: list[ModuleGraphLink]


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
