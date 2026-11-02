@echo off
setlocal
cd /d %~dp0

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1

echo ============================================================
echo MFI-Edge Stage 24 - Residual/Error Suppression STRICT
echo Native GT + one-to-one evaluation + nested selection
echo Canonical matcher used for every scientific threshold
echo ============================================================

if exist automation\STOP_STAGE24 (
  echo ERROR: automation\STOP_STAGE24 exists.
  echo Delete it only when you intend to resume/start Stage 24.
  exit /b 3
)

if exist .venv\Scripts\python.exe call .venv\Scripts\activate.bat

python run_stage24_preflight.py
if errorlevel 1 (
  echo.
  echo STAGE 24 BLOCKED: preflight failed.
  exit /b %errorlevel%
)

python -c "import sys; sys.path.insert(0, r'%CD%'); import run_stage24_residual_campaign_strict as m; raise SystemExit(m.main())" %*
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo.
  echo STAGE 24 STOPPED WITH ERROR %RC%
  echo See results\local_dev\stage24_residual_suppression\
  exit /b %RC%
)

echo.
echo STAGE 24 FINISHED SAFELY
echo Results: results\local_dev\stage24_residual_suppression\
endlocal
