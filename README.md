# Project Atlas

Read-only localhost dashboard that maps one local codebase into plain-English app parts and builds scoped SMAC sniper prompts.

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

1. Pick a project folder.
2. Pick the app part you want SMAC to inspect.
3. Pick the job: `Diagnose bug`, `Audit quality`, or `Cleanup risk`.
4. Click `Pull trigger`.
5. Atlas copies a ready `$smac` prompt with the right files, avoid zones, checks, and escalation rules.

Atlas does not run agents silently. You paste the prompt into Claude or Codex and send it.

## Friend Install Notes

Project Atlas searches the folder above its install folder, plus common folders such as Projects, Desktop, and Documents. It does not require any machine-specific path.

Runtime data stays under `.atlas/` and is ignored by git.
