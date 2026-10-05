@echo off
setlocal
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo [MFI-Edge] Creating Python virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-webui.txt
python run_webui.py
endlocal
