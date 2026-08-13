$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment not found. Run: python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt"
}

Write-Host "Installing build dependencies..."
& $python -m pip install -q setuptools wheel

Write-Host "Building Windows release (this may take several minutes)..."
& $python setup.py build_apps

$releaseDir = Join-Path $ProjectRoot "build\win_amd64"
$releaseExe = Join-Path $releaseDir "get_level_of_monkey.exe"
if (Test-Path $releaseExe) {
    Write-Host ""
    Write-Host "Release ready:" -ForegroundColor Green
    Write-Host "  $releaseExe"
    Write-Host ""
    Write-Host "Copy the whole folder 'build\win_amd64' to distribute the game."
} else {
    Write-Host "Build finished. Check build\ for output folders." -ForegroundColor Yellow
}
