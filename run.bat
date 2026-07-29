@echo off
rem Ярлык запуска botyaraTD для Windows (CMD)

cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python main.py %*
pause
