param(
  [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Stop"

while ($true) {
  try {
    & (Join-Path $PSScriptRoot "sync.ps1") -Message "sync: automatic workspace update"
  } catch {
    Write-Warning $_
  }

  Start-Sleep -Seconds $IntervalSeconds
}
