from pathlib import Path

from atlas_backend.graph import build_module_graph
from atlas_backend.module_infer import infer_modules
from atlas_backend.scanner import scan_repo


def test_deep_map_captures_files_tools_routes_scripts_and_risk(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"scripts":{"build":"vite build","test":"vitest run"},"dependencies":{"react":"latest","vite":"latest"}}',
        encoding="utf-8",
    )
    (sample_repo / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.115", "pydantic>=2"]\n[project.scripts]\nsample-api = "app.api:main"\n',
        encoding="utf-8",
    )
    (sample_repo / "app" / "api.py").write_text(
        'from fastapi import FastAPI\nfrom app.core.governor import govern\n\napp = FastAPI()\n\n@app.post("/run")\ndef run_route() -> str:\n    return govern(" ok ")\n\ndef main() -> None:\n    pass\n',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    nodes = {node.id: node for node in graph.nodes}
    links = {(link.source, link.target, link.label) for link in graph.links}

    assert nodes["file:app/api.py"].layer == "files"
    assert nodes["tool:python:fastapi"].layer == "tools"
    assert nodes["tool:npm:react"].layer == "tools"
    assert nodes["pipeline:route:app/api.py:post:/run"].layer == "pipelines"
    assert nodes["pipeline:npm:build"].layer == "pipelines"
    assert nodes["risk:docs"].layer == "risk"
    assert ("file:app/api.py", "file:app/core/governor.py", "uses") in links
    assert ("tests", "python-core", "checks") in links


def test_deep_map_nodes_can_aim_smac_through_module_id(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"dependencies":{"react":"latest"}}',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    nodes = {node.id: node for node in graph.nodes}

    assert nodes["file:app/core/engine.py"].module_id == "python-core"
    assert nodes["tool:npm:react"].module_id == "frontend"


def test_pipeline_story_maps_transcription_workflow_as_stations(sample_repo: Path) -> None:
    (sample_repo / "requirements.txt").write_text(
        "demucs\npyannote.audio\nopenai\nfaster-whisper\n",
        encoding="utf-8",
    )
    (sample_repo / "app" / "pipeline.py").write_text(
        "import demucs\nimport pyannote.audio\nfrom faster_whisper import WhisperModel\nfrom openai import OpenAI\n\n"
        "def process_video(video_file: str) -> str:\n"
        "    vocals = separate_vocal_stem(video_file)\n"
        "    speakers = diarize_speakers(vocals)\n"
        "    transcript = transcribe_audio(vocals, speakers)\n"
        "    return clean_transcript_with_ai(transcript)\n",
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    workflow_nodes = [node for node in graph.nodes if node.layer == "workflow"]
    workflow_links = [(link.source, link.target, link.label) for link in graph.links if link.layer == "workflow"]

    labels = [node.label for node in workflow_nodes]
    assert labels == [
        "Video files",
        "Stem splitter",
        "Speaker labels",
        "Speech to text",
        "AI cleanup",
        "Final transcript",
    ]
    assert all(node.kind == "pipeline-stage" for node in workflow_nodes)
    assert all(node.module_id == "python-core" for node in workflow_nodes)
    assert workflow_links == [
        ("workflow:input", "workflow:stem-splitter", "then"),
        ("workflow:stem-splitter", "workflow:diarization", "then"),
        ("workflow:diarization", "workflow:transcription", "then"),
        ("workflow:transcription", "workflow:ai-cleanup", "then"),
        ("workflow:ai-cleanup", "workflow:output", "then"),
    ]



def test_generic_app_workflow_uses_real_project_parts_not_transcription_template(sample_repo: Path) -> None:
    (sample_repo / "package.json").write_text(
        '{"scripts":{"build":"vite build"},"dependencies":{"react":"latest","vite":"latest"}}',
        encoding="utf-8",
    )
    (sample_repo / "app" / "api.py").write_text(
        'from fastapi import FastAPI\nfrom app.core.governor import govern\n\napp = FastAPI()\n\n@app.post("/run")\ndef run_route() -> str:\n    return govern(" ok ")\n',
        encoding="utf-8",
    )
    (sample_repo / "app" / "db.py").write_text(
        'def save_result(value: str) -> None:\n    pass\n',
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    labels = [node.label for node in graph.nodes if node.layer == "workflow"]

    assert "Screen and buttons" in labels
    assert "API routes" in labels
    assert "Main engine" in labels
    assert "Data and storage" in labels
    assert "External tools" in labels
    assert "Stem splitter" not in labels
    assert "Speaker labels" not in labels
    assert "Speech to text" not in labels
    assert "Final transcript" not in labels


def test_transcription_workflow_does_not_invent_missing_stations(sample_repo: Path) -> None:
    (sample_repo / "requirements.txt").write_text(
        "demucs\nopenai\nfaster-whisper\n",
        encoding="utf-8",
    )
    (sample_repo / "app" / "pipeline.py").write_text(
        "import demucs\nfrom faster_whisper import WhisperModel\nfrom openai import OpenAI\n\n"
        "def process_video(video_file: str) -> str:\n"
        "    vocals = separate_vocal_stem(video_file)\n"
        "    transcript = transcribe_audio(vocals)\n"
        "    return clean_transcript_with_ai(transcript)\n",
        encoding="utf-8",
    )

    scan = scan_repo(sample_repo)
    graph = build_module_graph(scan, infer_modules(scan))
    labels = [node.label for node in graph.nodes if node.layer == "workflow"]

    assert "Stem splitter" in labels
    assert "Speech to text" in labels
    assert "AI cleanup" in labels
    assert "Speaker labels" not in labels
