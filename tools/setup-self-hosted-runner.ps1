[CmdletBinding()]
param(
    [string]$RunnerRoot = 'C:\actions-runner-control_android',
    [string]$Repository = 'https://github.com/bilamsaovaytroi-max/control_android',
    [string]$RunnerVersion = ''
)

$ErrorActionPreference = 'Stop'

Write-Host 'This script never stores or accepts a runner token as a command-line argument.'
$token = Read-Host 'Enter a newly generated GitHub runner registration token' -AsSecureString
$tokenPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
try {
    $tokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPtr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPtr)
}

New-Item -ItemType Directory -Force -Path $RunnerRoot | Out-Null

if ([string]::IsNullOrWhiteSpace($RunnerVersion)) {
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest' -Headers @{ Accept = 'application/vnd.github+json' }
    $RunnerVersion = $release.tag_name.TrimStart('v')
}

$archive = Join-Path $RunnerRoot "actions-runner-win-x64-$RunnerVersion.zip"
$download = "https://github.com/actions/runner/releases/download/v$RunnerVersion/actions-runner-win-x64-$RunnerVersion.zip"
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $download -OutFile $archive
}

if (-not (Test-Path -LiteralPath (Join-Path $RunnerRoot 'config.cmd'))) {
    Expand-Archive -LiteralPath $archive -DestinationPath $RunnerRoot -Force
}

Push-Location $RunnerRoot
try {
    & .\config.cmd --unattended --url $Repository --token $tokenPlain --name "$env:COMPUTERNAME-control_android" --labels 'control_android' --work '_work' --replace
    if ($LASTEXITCODE -ne 0) { throw "Runner configuration failed with exit code $LASTEXITCODE" }
}
finally {
    $tokenPlain = $null
    Pop-Location
}

Write-Host "Runner configured at $RunnerRoot. Start it with .\run.cmd from that directory."
