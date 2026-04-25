import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class AtlasDB:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS repos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL UNIQUE,
                    head_commit TEXT,
                    scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    is_test INTEGER NOT NULL CHECK (is_test IN (0, 1)),
                    UNIQUE(repo_id, path)
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_line INTEGER,
                    quote TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    freshness TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(
                    subject,
                    quote,
                    source_file,
                    content='evidence',
                    content_rowid='id'
                );

                CREATE TABLE IF NOT EXISTS modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    freshness TEXT NOT NULL,
                    reachability TEXT NOT NULL,
                    UNIQUE(repo_id, name)
                );

                CREATE TABLE IF NOT EXISTS module_files (
                    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    role TEXT NOT NULL,
                    PRIMARY KEY(module_id, file_path, role)
                );

                CREATE TABLE IF NOT EXISTS packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
                    module_name TEXT NOT NULL,
                    question TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    needs_full_smac INTEGER NOT NULL CHECK (needs_full_smac IN (0, 1)),
                    destructive_actions_allowed INTEGER NOT NULL CHECK (destructive_actions_allowed IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    packet_id INTEGER NOT NULL REFERENCES packets(id) ON DELETE CASCADE,
                    packet_minutes REAL NOT NULL,
                    manual_minutes REAL NOT NULL,
                    packet_accepted_findings INTEGER NOT NULL,
                    manual_accepted_findings INTEGER NOT NULL,
                    beats_manual INTEGER NOT NULL CHECK (beats_manual IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def table_names(self) -> set[str]:
        with self.connect() as connection:
            rows = connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')").fetchall()
        return {str(row["name"]) for row in rows}

    def pragma(self, name: str) -> Any:
        with self.connect() as connection:
            row = connection.execute(f"PRAGMA {name}").fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            cursor = connection.execute(sql, tuple(params))
            rows = cursor.fetchall()
            connection.commit()
        return rows