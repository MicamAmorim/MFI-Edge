@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo STAGE24G-L: preflight, corrected pair scores, aggregation, triples, suppression, native GT, official BSDS.
echo Press Ctrl+C to interrupt or create automation\STOP_STAGE24_PAPER_A for checkpoint-safe stop.
"%PYTHON%" "run_stage24_paper_a_recertification.py" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo STAGE24G-L exited with error code %EXITCODE%.
  exit /b %EXITCODE%
)
echo STAGE24G-L command completed.
exit /b 0
