@echo off
setlocal
cd /d %~dp0

if not defined MFI_RESEARCH_ROOT (
  if exist "%~dp0..\MFI-Edge\results\local_dev\stage12d_bipolar_cv\frozen_candidates.json" (
    set "MFI_RESEARCH_ROOT=%~dp0..\MFI-Edge"
  )
)

if defined MFI_RESEARCH_ROOT (
  echo [MFI-Edge] Research artifacts: %MFI_RESEARCH_ROOT%
) else (
  echo [MFI-Edge] Research artifacts not auto-detected.
  echo [MFI-Edge] Set MFI_RESEARCH_ROOT to the active mfi-edge-local-dev worktree to enable Stage 12/14 models.
)

if not exist .venv\Scripts\python.exe (
  echo [MFI-Edge] Creating Python virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-webui.txt
python run_webui.py
endlocal
