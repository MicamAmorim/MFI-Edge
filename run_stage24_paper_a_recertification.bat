@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  echo ERROR: .venv\Scripts\python.exe not found. Activate/create project virtualenv first.
  exit /b 2
)
echo [1/3] Stage24G-L Python syntax validation
"%PYTHON%" -m compileall -q "src\postprocess.py" "src\stage24_strict_generalized_cf1f2.py" "src\stage24_math_contracts.py" "src\stage24_recertification_ops.py" "src\stage24_recertification_cv.py" "src\stage24_paper_a_controls.py" "src\stage24_paper_a_historical.py" "src\stage24_paper_a_berkeley_bootstrap.py" "src\stage24_paper_a_runtime.py" "run_stage24_paper_a_recertification.py" "scripts\prepare_stage24gl_paper_a_archive.py"
if errorlevel 1 (
  echo ERROR: syntax validation FAILED; campaign not started.
  exit /b 3
)
echo [2/3] Synthetic scientific integrity tests
"%PYTHON%" "tests\test_stage24_recertification.py"
if errorlevel 1 (
  echo ERROR: existing Stage24 unit tests FAILED.
  exit /b 4
)
"%PYTHON%" "tests\test_stage24_signed_nms.py"
if errorlevel 1 (
  echo ERROR: 45/135 degree NMS regression tests FAILED.
  exit /b 5
)
"%PYTHON%" "tests\test_stage24_math_contracts.py"
if errorlevel 1 (
  echo ERROR: tests FAILED; campaign not started.
  exit /b 4
)
echo [3/3] Running Stage24G-L. Stop safely with .\stop_stage24_paper_a_safely.bat
"%PYTHON%" "run_stage24_paper_a_recertification.py" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo ERROR: Stage24G-L exited with code %EXITCODE%. Inspect checkpoint/output.
  exit /b %EXITCODE%
)
echo Stage24G-L command completed; see claim_status.csv for scientific status.
exit /b 0
