@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  echo ERROR: .venv\Scripts\python.exe not found. Create the project virtualenv first.
  exit /b 2
)

echo [1/3] Stage24G-L source and test syntax validation
"%PYTHON%" -m compileall -q "test_math.py" "synthetic_v2.py" "src\postprocess.py" "src\stage24_strict_generalized_cf1f2.py" "src\stage24_math_contracts.py" "src\stage24_recertification_ops.py" "src\stage24_recertification_cv.py" "src\stage24_paper_a_controls.py" "src\stage24_paper_a_historical.py" "src\stage24_paper_a_berkeley_bootstrap.py" "src\stage24_paper_a_runtime.py" "scripts\capture_stage24gl_environment.py" "run_stage24_paper_a_recertification.py" "scripts\prepare_stage24gl_paper_a_archive.py" "scripts\build_stage24gl_repro_package.py" "scripts\verify_stage24gl_repro.py" "tests\test_stage24_repro_package.py" "tests\test_stage24_recertification.py" "tests\test_stage24_signed_nms.py" "tests\test_stage24_math_contracts.py" "tests\test_synthetic_line_offset.py"
if errorlevel 1 (
  echo ERROR: Python syntax validation FAILED; campaign not started.
  exit /b 3
)

echo [2/3] Mathematical, NMS, baseline and synthetic regressions
"%PYTHON%" -m unittest -v test_math
if errorlevel 1 (
  echo ERROR: legacy math tests FAILED; campaign not started.
  exit /b 4
)
"%PYTHON%" "tests\test_stage24_recertification.py"
if errorlevel 1 (
  echo ERROR: Stage24 math/science tests FAILED; campaign not started.
  exit /b 5
)
"%PYTHON%" "tests\test_stage24_signed_nms.py"
if errorlevel 1 (
  echo ERROR: signed diagonal NMS tests FAILED; campaign not started.
  exit /b 6
)
"%PYTHON%" "tests\test_stage24_math_contracts.py"
if errorlevel 1 (
  echo ERROR: generalized Choquet/capacity tests FAILED; campaign not started.
  exit /b 7
)
"%PYTHON%" "tests\test_synthetic_line_offset.py"
if errorlevel 1 (
  echo ERROR: historical/offset synthetic contract FAILED; campaign not started.
  exit /b 8
)

"%PYTHON%" "tests\test_stage24_repro_package.py"
if errorlevel 1 (
  echo ERROR: scientific reproducibility archive regression FAILED.
  exit /b 9
)

echo [3/3] Campaign phase and exact scientific environment capture
"%PYTHON%" "run_stage24_paper_a_recertification.py" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo ERROR: Stage24G-L exited with code %EXITCODE%. Inspect checkpoint/output.
  exit /b %EXITCODE%
)
echo Stage24G-L phase completed; inspect claim_status.csv before scientific claims.
exit /b 0
