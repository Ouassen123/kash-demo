$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DockerComposeFile = Join-Path $ProjectRoot 'docker\dev-compose.yml'
$FrontendDir = Join-Path $ProjectRoot 'frontend'
$HealthCheckScript = Join-Path $ProjectRoot 'scripts\habits_health_check.py'
$SmokeTestScript = Join-Path $ProjectRoot 'scripts\test_habits_multimodal.py'
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

function Write-Section {
    param([string]$Title)
    Write-Host ''
    Write-Host ('=' * 72)
    Write-Host $Title
    Write-Host ('=' * 72)
}

function Test-Url {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSec = 5
    )

    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Wait-ForUrl {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Label,
        [int]$TimeoutSec = 180,
        [int]$PollSec = 3
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Url -Url $Url -TimeoutSec 5) {
            Write-Host "[OK] $Label is reachable at $Url"
            return
        }
        Start-Sleep -Seconds $PollSec
    }

    throw "$Label did not become reachable within $TimeoutSec seconds: $Url"
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    if (Test-Path $VenvPython) {
        & $VenvPython $ScriptPath @Arguments
    }
    else {
        python $ScriptPath @Arguments
    }
}

Write-Section 'KASH local stack launcher'
Write-Host "Project root: $ProjectRoot"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is not installed or not available in PATH.'
}

Write-Section 'Cleaning existing containers'
try {
    docker compose -f $DockerComposeFile down --remove-orphans
} catch {
    Write-Host '[WARN] docker compose down reported an issue; continuing with explicit container cleanup.'
}

foreach ($containerName in @('kash-api', 'kash-pgadmin', 'kash-postgres')) {
    try {
        docker rm -f $containerName | Out-Null
    } catch {
        # Ignore missing containers.
    }
}

Write-Section 'Rebuilding Docker services'
docker compose -f $DockerComposeFile up -d --build postgres api pgadmin

Write-Section 'Waiting for backend'
Wait-ForUrl -Url 'http://localhost:8000/health' -Label 'FastAPI backend' -TimeoutSec 240 -PollSec 5

Write-Section 'Starting frontend if needed'
if (-not (Test-Url -Url 'http://localhost:3000' -TimeoutSec 5)) {
    Start-Process -FilePath 'npm.cmd' -ArgumentList 'run dev' -WorkingDirectory $FrontendDir | Out-Null
    Write-Host '[OK] Frontend dev server launched.'
}
else {
    Write-Host '[OK] Frontend already reachable.'
}

Write-Section 'Waiting for frontend'
Wait-ForUrl -Url 'http://localhost:3000' -Label 'Next.js frontend' -TimeoutSec 240 -PollSec 5

Write-Section 'Running launch health check'
Invoke-PythonScript -ScriptPath $HealthCheckScript

Write-Section 'Running multimodal Habits smoke test'
Invoke-PythonScript -ScriptPath $SmokeTestScript

Write-Section 'Done'
Write-Host 'Local stack is up and the Habits multimodal smoke test passed.'
