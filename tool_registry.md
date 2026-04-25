# Tool Registry

- Registry schema: v1.0
- Updated: 2026-04-25

## Project Atlas

- Version: 0.4.2
- Entry points: `atlas_backend/cli.py`, `atlas_backend/api.py`, `atlas_backend/graph.py`, `dashboard/src/App.tsx`, `dashboard/src/components/ModuleMap.tsx`
- Verification commands: `python -m pytest -q`, `npm test`, `npm run build`
- Local launch: backend on `127.0.0.1:8765`, dashboard on `127.0.0.1:5177`
- Install scripts: `install.ps1`, `start.ps1`
- Ingest behavior: auto-loads real local project folders, then waits for an explicit folder click; no automatic project scan.
- Main behavior: draws a layered visual module map for app parts, files, tools, pipelines, and risk zones; lets the user click a node to aim SMAC; then builds scoped `$smac` sniper prompts when the user clicks `Pull trigger`.
- Deep map behavior: detects package manifests, Python dependencies, npm scripts, Python entry points, backend routes, local imports, external libraries, tests, and risky unknown zones.
- Map display behavior: overview keeps high-level wires; files, tools, and pipelines are grouped into readable cards instead of listing every detected file or dependency as a node.
- AI review behavior: builds a local prompt from map facts for Claude or Codex review. It does not auto-send source code or run fixes.
- Safety: v1 is read-only. No auto-fix, no auto-delete, no auto-reorganize.
- Kill condition: if scoped prompts do not beat manual SMAC prompts on time saved or accepted findings, stop expanding Atlas beyond read-only mapping.
