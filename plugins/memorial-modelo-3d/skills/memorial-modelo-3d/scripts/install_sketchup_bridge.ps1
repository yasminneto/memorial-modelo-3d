[CmdletBinding()]
param([string]$SketchUpVersion = '2026')

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $skillRoot 'assets\sketchup_bridge'
$plugins = Join-Path $env:APPDATA "SketchUp\SketchUp $SketchUpVersion\SketchUp\Plugins"

if (-not (Test-Path -LiteralPath $source)) {
  throw "Bridge source not found: $source"
}

New-Item -ItemType Directory -Force -Path $plugins | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'Codex_Memorial3D.rb') -Destination $plugins -Force
Copy-Item -LiteralPath (Join-Path $source 'Codex_Memorial3D') -Destination $plugins -Recurse -Force

[pscustomobject]@{
  Installed = $true
  PluginsPath = $plugins
  Loader = Join-Path $plugins 'Codex_Memorial3D.rb'
}
