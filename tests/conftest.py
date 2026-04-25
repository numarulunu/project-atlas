from pathlib import Path

import pytest


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-app"
    (repo / "app" / "core").mkdir(parents=True)
    (repo / "frontend" / "src").mkdir(parents=True)
    (repo / "tests" / "core").mkdir(parents=True)
    (repo / "scripts").mkdir(parents=True)

    (repo / "README.md").write_text("# Sample App\n", encoding="utf-8")
    (repo / "app" / "core" / "engine.py").write_text(
        "def run_engine(value: str) -> str:\n    return value.strip()\n",
        encoding="utf-8",
    )
    (repo / "app" / "core" / "governor.py").write_text(
        "from app.core.engine import run_engine\n\n\ndef govern(value: str) -> str:\n    return run_engine(value)\n",
        encoding="utf-8",
    )
    (repo / "frontend" / "src" / "App.jsx").write_text(
        "import React from 'react';\n\nexport function App() {\n  return <button>Run</button>;\n}\n",
        encoding="utf-8",
    )
    (repo / "frontend" / "src" / "App.test.jsx").write_text(
        "import { App } from './App.jsx';\n",
        encoding="utf-8",
    )
    (repo / "tests" / "core" / "test_engine.py").write_text(
        "from app.core.engine import run_engine\n\n\ndef test_run_engine() -> None:\n    assert run_engine(' ok ') == 'ok'\n",
        encoding="utf-8",
    )
    (repo / "scripts" / "check.py").write_text("print('ok')\n", encoding="utf-8")
    return repo
