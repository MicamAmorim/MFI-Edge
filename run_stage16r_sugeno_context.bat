@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: repository Python environment not found at .venv\Scripts\python.exe
  exit /b 2
)

".venv\Scripts\python.exe" "run_stage16r_sugeno_context.py" %*
set RC=%ERRORLEVEL%
endlocal & exit /b %RC%
