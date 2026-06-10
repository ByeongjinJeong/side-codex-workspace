param(
  [string]$Message = "sync: update workspace"
)

$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repo

git pull --rebase --autostash
git add .

$changes = git status --porcelain
if (-not $changes) {
  Write-Host "nothing to commit"
  exit 0
}

git commit -m $Message
git push
