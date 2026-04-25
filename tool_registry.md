# Tool Registry

- Registry schema: v1.0
- Updated: 2026-04-25

## Project Atlas

- Version: 0.2.1
- Entry points: `atlas_backend/cli.py`, `atlas_backend/api.py`, `dashboard/src/App.tsx`
- Verification commands: `python -m pytest -q`, `npm test`, `npm run build`
- Local launch: backend on `127.0.0.1:8765`, dashboard on `127.0.0.1:5177`
- Install scripts: `install.ps1`, `start.ps1`
- Ingest behavior: starts with an explicit folder picker; no automatic project scan.
- Main behavior: builds scoped `$smac` sniper prompts and copies them when the user clicks `Pull trigger`.
- Safety: v1 is read-only. No auto-fix, no auto-delete, no auto-reorganize.
- Kill condition: if scoped prompts do not beat manual SMAC prompts on time saved or accepted findings, stop expanding Atlas beyond read-only mapping.
