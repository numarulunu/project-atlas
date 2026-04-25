from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AtlasConfig:
    data_dir: Path
    db_path: Path
    log_path: Path
    projects_root: Path


def default_config() -> AtlasConfig:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / ".atlas"
    return AtlasConfig(
        data_dir=data_dir,
        db_path=data_dir / "atlas.db",
        log_path=data_dir / "_atlas.log",
        projects_root=project_root.parent,
    )
