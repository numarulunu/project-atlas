# Tool Registry

- Registry schema: v1.0
- Updated: 2026-04-26

## Project Atlas

- Version: 0.5.1
- Entry points: `atlas_backend/cli.py`, `atlas_backend/api.py`, `atlas_backend/graph.py`, `dashboard/src/App.tsx`, `dashboard/src/components/ModuleMap.tsx`
- Verification commands: `python -m pytest -q`, `npm test`, `npm run build`
- Local launch: backend on `127.0.0.1:8765`, dashboard on `127.0.0.1:5177`
- Install scripts: `install.ps1`, `start.ps1`
- Ingest behavior: auto-loads real local project folders, then waits for an explicit folder click; no automatic project scan.
- Main behavior: draws an n8n-style workflow story map from the project's actual parts first, then keeps grouped layers for app parts, files, tools, pipelines, and risk zones. Clicking a station or node aims SMAC; `Pull trigger` builds a scoped `$smac` sniper prompt.
- Deep map behavior: detects package manifests, Python dependencies, npm scripts, Python entry points, backend routes, local imports, external libraries, tests, and risky unknown zones.
- Map display behavior: workflow view shows large processing stations with important arrows only. Transcription stations appear only for transcription-like projects; other projects use detected screens, routes, commands, engine, storage, tools, and tests. Overview keeps high-level wires; files, tools, and pipelines are grouped into readable cards instead of listing every detected file or dependency as a node.
- AI review behavior: builds a local prompt from map facts for Claude or Codex review. It does not auto-send source code or run fixes.
- Safety: v1 is read-only. No auto-fix, no auto-delete, no auto-reorganize.
- Kill condition: if scoped prompts do not beat manual SMAC prompts on time saved or accepted findings, stop expanding Atlas beyond read-only mapping.
