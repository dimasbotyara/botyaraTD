# Ярлык запуска botyaraTD для Windows (PowerShell)

Set-Location -Path $PSScriptRoot

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

python main.py $args
