@echo off
cd /d "%~dp0"
set "NODE_DIR=%LOCALAPPDATA%\nodejs\node-v22.11.0-win-x64"

if not exist .venv (
  echo Creando entorno virtual e instalando dependencias de Python...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist "%NODE_DIR%\node.exe" (
  echo Node.js no encontrado en %NODE_DIR%.
  echo Instala Node.js LTS desde https://nodejs.org/ y vuelve a correr este script.
  pause
  exit /b 1
)

start "LeadHunter API" cmd /k "".venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
start "LeadHunter Frontend" cmd /k ""cd /d "%~dp0frontend" && "%NODE_DIR%\node.exe" "%NODE_DIR%\node_modules\npm\bin\npm-cli.js" install && "%NODE_DIR%\node.exe" "%NODE_DIR%\node_modules\npm\bin\npm-cli.js" run dev -- --hostname 0.0.0.0 --port 3000""

echo LeadHunter arrancando con Next.js + FastAPI.
echo Frontend: http://localhost:3000
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
pause
