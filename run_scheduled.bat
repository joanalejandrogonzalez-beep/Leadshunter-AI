@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python scheduled.py >> data\scheduled.log 2>&1
