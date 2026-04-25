# Tool Registry

- Registry schema: v1.0
- Updated: 2026-04-25

## Project Atlas

- Version: 0.3.0
- Entry points: `atlas_backend/cli.py`, `atlas_backend/api.py`, `atlas_backend/graph.py`, `dashboard/src/App.tsx`, `dashboard/src/components/ModuleMap.tsx`
- Verification commands: `python -m pytest -q`, `npm test`, `npm run build`
- Local launch: backend on `127.0.0.1:8765`, dashboard on `127.0.0.1:5177`
- Install scripts: `install.ps1`, `start.ps1`
- Ingest behavior: auto-loads real local project folders, then waits for an explicit folder click; no automatic project scan.
- Main behavior: draws a visual module map, lets the user click a node to aim SMAC, then builds scoped `$smac` sniper prompts when the user clicks `Pull trigger`.
- Safety: v1 is read-only. No auto-fix, no auto-delete, no auto-reorganize.
- Kill condition: if scoped prompts do not beat manual SMAC prompts on time saved or accepted findings, stop expanding Atlas beyond read-only mapping.
