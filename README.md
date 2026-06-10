# side-codex-workspace

Personal Codex workspace for side projects.

This repo is intended to sync only files that should be portable between
Windows and macOS:

- `skills/`: personal Codex skills maintained by this repo
- `projects/`: side-project working notes or shared project scaffolds
- `scripts/`: install and sync helpers

Do not put the whole `~/.codex` directory in Git. It contains auth, logs,
sessions, caches, SQLite state, and machine-specific files.

## Windows setup

Clone the repo:

```powershell
git clone https://github.com/ByeongjinJeong/side-codex-workspace.git $env:USERPROFILE\side-codex-workspace
cd $env:USERPROFILE\side-codex-workspace
```

Link repo-managed skills into Codex:

```powershell
.\scripts\install-windows.ps1
```

Sync changes:

```powershell
.\scripts\sync.ps1
```

Optional continuous sync while working:

```powershell
.\scripts\watch-sync.ps1
```

## macOS setup

Clone the repo:

```bash
git clone https://github.com/ByeongjinJeong/side-codex-workspace.git ~/side-codex-workspace
cd ~/side-codex-workspace
```

Link repo-managed skills into Codex:

```bash
./scripts/install-mac.sh
```

Sync changes:

```bash
./scripts/sync.sh
```

Optional continuous sync while working:

```bash
./scripts/watch-sync.sh
```

## Adding a new personal skill

Create a folder under `skills/`:

```text
skills/my-skill/
  SKILL.md
```

Then run the install script for your OS. The script links each folder in
`skills/` into the Codex skills directory without overwriting existing skills.
