# Project Atlas Visual Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-load real local projects and show a click-to-aim visual module map built from the scanned project.

**Architecture:** Keep Atlas read-only. The backend still scans local files and infers modules, then adds a small graph object with module nodes and detected relationships. The dashboard renders that graph as a node map and uses node clicks to choose the SMAC target.

**Tech Stack:** Python FastAPI backend, pytest, React/Vite dashboard, Vitest.

---

### Task 1: Backend Project Roots

**Files:**
- Modify: `atlas_backend/api.py`
- Test: `tests/test_project_discovery.py`

- [ ] Add a failing test that creates a fake home with the shared desktop workspace, `Projects`, `Desktop`, and `Documents`, then asserts `project_search_roots()` includes the shared desktop workspace before broad folders and removes duplicates.
- [ ] Update `project_search_roots()` to search the configured parent, the shared desktop workspace, `Projects`, `Desktop`, and `Documents`.
- [ ] Run `python -m pytest tests/test_project_discovery.py -q` and confirm it passes.

### Task 2: Backend Module Graph

**Files:**
- Create: `atlas_backend/graph.py`
- Modify: `atlas_backend/models.py`
- Modify: `atlas_backend/api.py`
- Test: `tests/test_module_graph.py`
- Test: `tests/test_api_readonly.py`

- [ ] Add failing tests for graph nodes and the `tests -> python-core` check link from the sample repo.
- [ ] Add graph dataclasses for node/link payloads.
- [ ] Build graph nodes from inferred modules with stable percent positions.
- [ ] Build graph links from mapped tests and import evidence.
- [ ] Include `graph` in `/api/repo/scan`.
- [ ] Run `python -m pytest tests/test_module_graph.py tests/test_api_readonly.py -q` and confirm it passes.

### Task 3: Dashboard Project Loading

**Files:**
- Modify: `dashboard/src/App.tsx`
- Modify: `dashboard/src/App.test.tsx`
- Modify: `dashboard/src/types.ts`

- [ ] Add a failing test that `/api/projects` returns a real project and the dashboard shows it without fake sample rows.
- [ ] Remove fake project fallback rows.
- [ ] Show clear loading, empty, and offline states while keeping manual path entry.
- [ ] Run `npm test` and confirm it passes.

### Task 4: Dashboard Visual Map

**Files:**
- Create: `dashboard/src/components/ModuleMap.tsx`
- Modify: `dashboard/src/App.tsx`
- Modify: `dashboard/src/styles.css`
- Modify: `dashboard/src/types.ts`
- Test: `dashboard/src/App.test.tsx`

- [ ] Add a failing test that selecting a real project renders `Project map`, clickable module nodes, and a visible relationship line label.
- [ ] Render graph links as SVG lines and labels.
- [ ] Render modules as clickable n8n-style nodes with plain-English names.
- [ ] Clicking a node updates the selected SMAC target.
- [ ] Run `npm test` and confirm it passes.

### Task 5: Verification and Release

**Files:**
- Modify: `tool_registry.md`
- Modify: version files if behavior changes are shipped.

- [ ] Bump Project Atlas to `0.3.0`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `npm test` in `dashboard`.
- [ ] Run `npm run build` in `dashboard`.
- [ ] Run current-tree and Git-history leak scans.
- [ ] Commit and push to GitHub.
- [ ] Restart the local backend/dashboard so the user sees the new version.
