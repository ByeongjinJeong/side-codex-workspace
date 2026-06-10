param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$CodexSkills = (Join-Path $env:USERPROFILE ".codex\skills")
)

$ErrorActionPreference = "Stop"

$RepoSkills = Join-Path $RepoRoot "skills"
New-Item -ItemType Directory -Force -Path $RepoSkills | Out-Null
New-Item -ItemType Directory -Force -Path $CodexSkills | Out-Null

Get-ChildItem -Path $RepoSkills -Directory | ForEach-Object {
  $name = $_.Name
  $target = $_.FullName
  $link = Join-Path $CodexSkills $name

  if (Test-Path -LiteralPath $link) {
    Write-Host "skip: $link already exists"
    return
  }

  New-Item -ItemType Junction -Path $link -Target $target | Out-Null
  Write-Host "linked: $link -> $target"
}
