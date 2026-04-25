# Project Atlas Deep Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the shallow module sketch with a layered deterministic map that captures project files, tools, libraries, routes, scripts, imports, tests, and risk zones.

**Architecture:** Keep Atlas read-only. The backend enriches `ModuleGraph` with typed nodes and typed links generated from manifests, imports, routes, scripts, and file paths. The dashboard filters the same graph into `Overview`, `Pipelines`, `Tools`, `Files`, and `Risk` layers without hiding the SMAC trigger.

**Tech Stack:** Python FastAPI backend, pytest, React/Vite dashboard, Vitest.

---

### Task 1: Deep Backend Graph

**Files:**
- Modify: `atlas_backend/models.py`
- Modify: `atlas_backend/graph.py`
- Test: `tests/test_deep_map.py`

- [x] Write tests proving file nodes, tool nodes, route nodes, script nodes, local import links, and risk nodes exist for a sample project.
- [x] Extend graph node/link models with `kind`, `layer`, `module_id`, `files`, and metadata.
- [x] Parse `package.json`, `pyproject.toml`, Python route decorators, npm scripts, Python scripts, local imports, external imports, and tests.
- [x] Run `python -m pytest tests/test_deep_map.py -q`.

### Task 2: API and Prompt Context

**Files:**
- Modify: `atlas_backend/api.py`
- Modify: `atlas_backend/prompt_builder.py`
- Test: `tests/test_api_readonly.py`
- Test: `tests/test_prompt_builder.py`

- [x] Ensure `/api/repo/scan` returns deep graph fields.
- [x] Add library/tool/import context to sniper prompts for the selected module.
- [x] Run targeted pytest tests.

### Task 3: Dashboard Layers

**Files:**
- Modify: `dashboard/src/types.ts`
- Modify: `dashboard/src/components/ModuleMap.tsx`
- Modify: `dashboard/src/styles.css`
- Modify: `dashboard/src/App.test.tsx`

- [x] Add tests for `Overview`, `Pipelines`, `Tools`, `Files`, and `Risk` layer buttons.
- [x] Render typed nodes with readable chips and counts.
- [x] Let file/tool/pipeline nodes aim SMAC through their `module_id`.
- [x] Run `npm test`.

### Task 4: Release

**Files:**
- Modify: `README.md`
- Modify: `tool_registry.md`
- Modify: version files

- [x] Bump to `0.4.0`.
- [x] Run `python -m pytest -q`.
- [x] Run `npm test` and `npm run build`.
- [x] Run current and history leak scans.
- [x] Commit, push, restart local Atlas.
