@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Creando entorno virtual e instalando dependencias...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Iniciando LeadHunter AI FastAPI Backend en http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
