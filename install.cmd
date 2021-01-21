@echo off

if not exist ".gitignore" (
    echo ERROR: must be run in the project directory
    exit 1
)

if not exist "venv" (
    python.exe -m venv venv
    .\venv\Scripts\python -m pip install --upgrade pip
)

.\venv\Scripts\pip install -r requirements.txt

pause
