@echo off
cd /d "%~dp0"
if not exist "data" mkdir data
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)
python scheduled.py >> data\scheduled.log 2>&1
