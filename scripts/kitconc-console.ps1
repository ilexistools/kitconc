# Start, stop or check the Kitconc MCP Console (kitconc-gui) on Windows.
#
#   scripts\kitconc-console.ps1 start   [--workspace DIR] [--port N] [--read-only] [--no-browser]
#   scripts\kitconc-console.ps1 stop    [--port N]
#   scripts\kitconc-console.ps1 status  [--port N]
#   scripts\kitconc-console.ps1 restart [same options as start]
#
# The server runs in the background (hidden window); its output goes to kitconc-gui.log in the
# repository root. Set KITCONC_PORT to change the default port (8787).
# Double-click start-gui.cmd / stop-gui.cmd for the common case.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root '.kitconc-gui.pid'
$LogFile = Join-Path $Root 'kitconc-gui.log'

$Command = 'start'
$Port = 8787
if ($env:KITCONC_PORT) { $Port = [int]$env:KITCONC_PORT }
$Workspace = $null
$ReadOnly = $false
$NoBrowser = $false

function Show-Usage {
    Write-Host 'Usage: kitconc-console.ps1 [start|stop|status|restart] [--workspace DIR] [--port N] [--read-only] [--no-browser]'
}

for ($i = 0; $i -lt $args.Count; $i++) {
    $arg = [string]$args[$i]
    if (@('start', 'stop', 'status', 'restart') -contains $arg) { $Command = $arg }
    elseif ($arg -eq '--workspace') { $i++; $Workspace = [string]$args[$i] }
    elseif ($arg -eq '--port') { $i++; $Port = [int]$args[$i] }
    elseif ($arg -eq '--read-only') { $ReadOnly = $true }
    elseif ($arg -eq '--no-browser') { $NoBrowser = $true }
    elseif (@('-h', '--help', '/?') -contains $arg) { Show-Usage; exit 0 }
    else { Write-Host "Unknown option: $arg" -ForegroundColor Red; Show-Usage; exit 2 }
}
if ($Port -lt 1 -or $Port -gt 65535) { Write-Host 'Port must be between 1 and 65535.' -ForegroundColor Red; exit 2 }
if ($Workspace) {
    if (-not [IO.Path]::IsPathRooted($Workspace)) { $Workspace = Join-Path (Get-Location).Path $Workspace }
    $Workspace = $Workspace.TrimEnd('\')
}
$Url = "http://127.0.0.1:$Port/"

function Get-ConsoleInfo {
    # Returns the console's /api/info, or $null when no Kitconc console answers on the port.
    try {
        $info = Invoke-RestMethod -Uri "$($Url)api/info" -TimeoutSec 2
        if ($info.name -eq 'kitconc') { return $info }
    } catch {}
    return $null
}

function Get-Listeners {
    try {
        return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique)
    } catch { return @() }
}

function Stop-Tree([int]$ProcessId) {
    foreach ($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)) {
        Stop-Tree ([int]$child.ProcessId)
    }
    try { Stop-Process -Id $ProcessId -Force -ErrorAction Stop } catch {}
}

function Get-SavedProcess {
    # The background process recorded at start, ignoring a stale PID reused by another program.
    if (-not (Test-Path $PidFile)) { return $null }
    try {
        $id = [int]((Get-Content $PidFile -Raw).Trim())
        $proc = Get-Process -Id $id -ErrorAction Stop
        $written = (Get-Item $PidFile).LastWriteTime
        if ($proc.ProcessName -eq 'cmd' -and [Math]::Abs(($proc.StartTime - $written).TotalSeconds) -lt 120) { return $proc }
    } catch {}
    return $null
}

function Show-Endpoints($info) {
    Write-Host ''
    Write-Host "  Console            $Url"
    Write-Host "  MCP (HTTP)         $($Url)mcp"
    Write-Host "  MCP (SSE)          $($Url)sse"
    Write-Host "  REST API           $($Url)api/tools"
    if ($info) {
        Write-Host "  Workspace          $($info.workspace)"
        Write-Host "  Version            $($info.version)$(if ($info.read_only) { ' (read-only)' })"
    }
    Write-Host ''
}

function Invoke-Start {
    $info = Get-ConsoleInfo
    if ($info) {
        Write-Host "Kitconc MCP Console is already running." -ForegroundColor Green
        Show-Endpoints $info
        if (-not $NoBrowser) { Start-Process $Url }
        return 0
    }
    if ((Get-Listeners).Count -gt 0) {
        Write-Host "Port $Port is used by another program. Choose another one with --port." -ForegroundColor Red
        return 1
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host 'uv was not found. Install it from https://docs.astral.sh/uv/ and try again.' -ForegroundColor Red
        return 1
    }

    # Install or update the environment first. If that fails while a usable environment exists
    # (typically because another Kitconc process holds files in .venv), start with it anyway.
    Write-Host 'Preparing the Python environment (the first run can take a few minutes)...'
    Push-Location $Root
    try {
        $syncOutput = & cmd /d /c "uv sync --locked --python 3.12 2>&1"
        $syncOk = ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
    $syncOutput | Out-File -FilePath $LogFile -Encoding utf8
    if (-not $syncOk) {
        if (Test-Path (Join-Path $Root '.venv\Scripts\python.exe')) {
            Write-Host 'Could not update the environment (is another Kitconc process running?); using the existing one.' -ForegroundColor Yellow
        } else {
            Write-Host 'uv could not create the environment:' -ForegroundColor Red
            $syncOutput | Select-Object -Last 20 | ForEach-Object { Write-Host "  $_" }
            return 1
        }
    }

    $guiArgs = @('run', '--locked', '--python', '3.12', '--no-sync', 'python', '-m', 'kitconc.agent.dashboard', '--no-browser', '--port', "$Port")
    if ($Workspace) { $guiArgs += @('--workspace', $Workspace) }
    if ($ReadOnly) { $guiArgs += '--read-only' }
    $quoted = ($guiArgs | ForEach-Object { if ($_ -match '[\s&|<>^()]') { '"' + $_ + '"' } else { $_ } }) -join ' '
    $commandLine = '/d /s /c "uv ' + $quoted + ' >> "' + $LogFile + '" 2>&1"'
    $proc = Start-Process -FilePath $env:ComSpec -ArgumentList $commandLine -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    Set-Content -Path $PidFile -Value $proc.Id -Encoding ascii

    Write-Host 'Starting Kitconc MCP Console' -NoNewline
    $deadline = (Get-Date).AddMinutes(5)
    while ((Get-Date) -lt $deadline) {
        $info = Get-ConsoleInfo
        if ($info) { break }
        if ($proc.HasExited) { break }
        Write-Host '.' -NoNewline
        Start-Sleep -Milliseconds 700
    }
    Write-Host ''
    if (-not $info) {
        Write-Host 'The console did not start. Last lines of kitconc-gui.log:' -ForegroundColor Red
        if (Test-Path $LogFile) { Get-Content $LogFile -Tail 20 | ForEach-Object { Write-Host "  $_" } }
        Stop-Tree $proc.Id
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return 1
    }
    Write-Host 'Kitconc MCP Console is running.' -ForegroundColor Green
    Show-Endpoints $info
    Write-Host "Stop it with stop-gui.cmd (or: scripts\kitconc-console.ps1 stop --port $Port)."
    if (-not $NoBrowser) { Start-Process $Url }
    return 0
}

function Invoke-Stop {
    $stopped = $false
    $saved = Get-SavedProcess
    if ($saved) { Stop-Tree $saved.Id; $stopped = $true }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

    # Also stop a console started another way (e.g. kitconc-gui in a terminal), but only after
    # confirming that the program on the port really is Kitconc.
    if (Get-ConsoleInfo) {
        foreach ($id in Get-Listeners) { Stop-Tree ([int]$id); $stopped = $true }
    }
    for ($i = 0; $i -lt 20 -and (Get-Listeners).Count -gt 0 -and $stopped; $i++) { Start-Sleep -Milliseconds 500 }

    if ($stopped) { Write-Host "Kitconc MCP Console stopped (port $Port)." -ForegroundColor Green }
    else { Write-Host "Kitconc MCP Console is not running on port $Port." }
    return 0
}

function Invoke-Status {
    $info = Get-ConsoleInfo
    if ($info) {
        Write-Host 'Kitconc MCP Console is running.' -ForegroundColor Green
        Show-Endpoints $info
        return 0
    }
    Write-Host "Kitconc MCP Console is not running on port $Port."
    return 3
}

switch ($Command) {
    'start'   { exit (Invoke-Start) }
    'stop'    { exit (Invoke-Stop) }
    'status'  { exit (Invoke-Status) }
    'restart' { Invoke-Stop | Out-Null; exit (Invoke-Start) }
}
