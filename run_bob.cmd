@echo off

if not exist ".gitignore" (
    echo ERROR: must be run in the project directory
    exit 1
)

if not exist "venv" (
    echo ERROR: run install.cmd first
    exit 1
)

.\venv\Scripts\python bob.py

pause
