$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPython = Join-Path $root "..\virt\Scripts\python.exe"
if (Test-Path $venvPython) {
	$python = $venvPython
} else {
	$python = "python"
}

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

# One-file Windows binary build for the PyQt6 application.
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name LANG-TRANS --icon Arabic.ico --add-data "assets;assets" Translator.py

Write-Host "Build complete. Check dist/LANG-TRANS.exe" -ForegroundColor Green
