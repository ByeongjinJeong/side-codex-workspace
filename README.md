# side-codex-workspace

Personal Codex workspace for side projects.

This repo is intended to sync only files that should be portable between
Windows and macOS:

- `skills/`: personal Codex skills maintained by this repo
- `projects/`: side-project working notes or shared project scaffolds
- `scripts/`: install and sync helpers

External tools such as gstack are not vendored into this repo. Keep only the
install notes here, then reinstall them from their upstream repositories on each
machine.

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

Install gstack for Codex:

```powershell
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$env:USERPROFILE\gstack"
cd "$env:USERPROFILE\gstack"
.\setup --host codex
```

Windows 11 needs Git, Bun, and Node.js on `PATH`.

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

Install gstack for Codex:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack
./setup --host codex
```

macOS needs Git and Bun on `PATH`.

## Adding a new personal skill

Create a folder under `skills/`:

```text
skills/my-skill/
  SKILL.md
```

Then run the install script for your OS. The script links each folder in
`skills/` into the Codex skills directory without overwriting existing skills.
