[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$ModelPath,
  [Parameter(Mandatory = $true)][string]$OutputDir,
  [string]$SketchUpVersion = '2026',
  [string]$SketchUpExe,
  [int]$SceneLimit = 100,
  [int]$MaxDepth = 8,
  [int]$RenderWidth = 1600,
  [int]$RenderHeight = 1000,
  [double]$TechnicalScaleFactor = 2.5,
  [string]$FocusSetsPath,
  [int]$TimeoutSeconds = 1800
)

$ErrorActionPreference = 'Stop'
$model = (Resolve-Path -LiteralPath $ModelPath).Path
$output = [System.IO.Path]::GetFullPath($OutputDir)
$exe = if ($SketchUpExe) { (Resolve-Path -LiteralPath $SketchUpExe).Path } else { Join-Path $env:ProgramFiles "SketchUp\SketchUp $SketchUpVersion\SketchUp\SketchUp.exe" }

if (-not (Test-Path -LiteralPath $exe)) {
  throw "SketchUp executable not found: $exe"
}

if ([IO.Path]::GetExtension($model) -ne '.skp') { throw 'ModelPath must be a .skp file.' }
if ((Test-Path -LiteralPath $output) -and (Get-ChildItem -LiteralPath $output -Force | Select-Object -First 1)) {
  throw 'Use a new or empty output directory to prevent stale job results and overwrites.'
}
$bridgeDir = Join-Path $env:APPDATA "SketchUp\SketchUp $SketchUpVersion\SketchUp\Plugins\Codex_Memorial3D"
if (Test-Path -LiteralPath (Join-Path $bridgeDir 'pending_job.json')) {
  throw 'Another extraction is pending. Inspect that job before starting a new one.'
}
if (Get-Process SketchUp -ErrorAction SilentlyContinue) {
  throw 'Save and close SketchUp before automatic extraction to preserve the active work session.'
}

& (Join-Path $PSScriptRoot 'install_sketchup_bridge.ps1') -SketchUpVersion $SketchUpVersion | Out-Null
New-Item -ItemType Directory -Force -Path $output | Out-Null

$jobPath = Join-Path $output 'job.json'
$job = [ordered]@{
  model_path = $model
  output_dir = $output
  scene_limit = $SceneLimit
  max_depth = $MaxDepth
  render_width = $RenderWidth
  render_height = $RenderHeight
  technical_scale_factor = $TechnicalScaleFactor
}
if ($FocusSetsPath) {
  $focusFile = (Resolve-Path -LiteralPath $FocusSetsPath).Path
  # Preserve a one-item JSON array as an array. Without -NoEnumerate,
  # PowerShell unwraps it and the SketchUp bridge receives a hash instead of
  # a list of focus definitions.
  $job.focus_sets = @(Get-Content -LiteralPath $focusFile -Raw | ConvertFrom-Json)
}
$json = $job | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($jobPath, $json, [Text.UTF8Encoding]::new($false))

$plugins = Join-Path $env:APPDATA "SketchUp\SketchUp $SketchUpVersion\SketchUp\Plugins"
$pendingJob = Join-Path $plugins 'Codex_Memorial3D\pending_job.json'
Copy-Item -LiteralPath $jobPath -Destination $pendingJob -Force
# Start-Process flattens ArgumentList to a command line. Quote the model explicitly
# so SketchUp receives paths containing spaces as one argument.
$quotedModel = '"' + $model.Replace('"', '\"') + '"'
$process = Start-Process -FilePath $exe -ArgumentList @($quotedModel) -WindowStyle Hidden -PassThru
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
$statusPath = Join-Path $output 'status.json'

while ([DateTime]::UtcNow -lt $deadline) {
  if (Test-Path -LiteralPath $statusPath) {
    try {
      $status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
      if ($status.status -eq 'complete') { break }
      if ($status.status -eq 'failed') {
        Remove-Item -LiteralPath $pendingJob -Force -ErrorAction SilentlyContinue
        throw "SketchUp extraction failed: $($status.message)"
      }
    } catch {
      if ($_.Exception.Message -like 'SketchUp extraction failed:*') { throw }
      # The status file may be between atomic-looking writes; retry.
    }
  }
  if ($process.HasExited -and -not (Test-Path -LiteralPath (Join-Path $output 'manifest.json'))) {
    Remove-Item -LiteralPath $pendingJob -Force -ErrorAction SilentlyContinue
    throw "SketchUp exited before producing a manifest. Exit code: $($process.ExitCode)"
  }
  Start-Sleep -Milliseconds 500
}

if (-not (Test-Path -LiteralPath (Join-Path $output 'manifest.json')) -or $status.status -ne 'complete') {
  Remove-Item -LiteralPath $pendingJob -Force -ErrorAction SilentlyContinue
  throw "Timed out waiting for SketchUp extraction after $TimeoutSeconds seconds."
}

[pscustomobject]@{
  Status = 'complete'
  Manifest = Join-Path $output 'manifest.json'
  RenderDirectory = Join-Path $output 'renders'
  ProcessId = $process.Id
}
