# Project Atlas

Read-only localhost dashboard that maps one local codebase into a deep visual app map and builds scoped SMAC sniper prompts.

Safety: no auto-fix, no auto-delete, no auto-reorganize.

## Install

```powershell
git clone https://github.com/numarulunu/project-atlas.git
cd project-atlas
.\install.ps1
```

## Local Launch

```powershell
cd project-atlas
.\start.ps1
```

Open `http://127.0.0.1:5177`.

## How It Works

1. Atlas auto-loads real project folders from common local work areas.
2. Pick a project folder.
3. Atlas draws a project-specific workflow story first. Transcription apps may show stations like input, splitter, transcription, AI cleanup, and output; other apps use their own screens, routes, commands, engine, storage, tools, and tests. Other tabs keep grouped app parts, folders, tools, tests, and risk zones.
4. Click the station or node you want SMAC to inspect.
5. Pick the job: `Diagnose bug`, `Audit quality`, or `Cleanup risk`.
6. Click `Pull trigger`.
7. Atlas copies a ready `$smac` prompt with the right files, avoid zones, checks, tools, workflow station context, nearby connections, and escalation rules.

Use `AI review map` when the map needs a smarter pass. Atlas builds a prompt from map facts so Claude or Codex can suggest better names, groups, missing links, and uncertain zones. Atlas does not send code automatically.

Atlas does not run agents silently. You paste the prompt into Claude or Codex and send it.

## Friend Install Notes

Project Atlas searches the folder above its install folder, plus common folders such as Projects, Desktop, Documents, and the shared desktop workspace. It does not require any machine-specific path.

Runtime data stays under `.atlas/` and is ignored by git.
