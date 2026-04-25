from pathlib import Path

from atlas_backend.db import AtlasDB


def test_schema_creates_core_tables(tmp_path: Path) -> None:
    db = AtlasDB(tmp_path / "atlas.db")
    db.initialize()
    expected = {"repos", "files", "evidence", "modules", "module_files", "packets", "audit_results"}
    assert expected.issubset(db.table_names())


def test_wal_mode_is_enabled(tmp_path: Path) -> None:
    db = AtlasDB(tmp_path / "atlas.db")
    db.initialize()
    assert db.pragma("journal_mode").lower() == "wal"