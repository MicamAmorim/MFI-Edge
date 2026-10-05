@echo off
setlocal
cd /d %~dp0

if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1

python run_stage12b_fuzzy_signature.py --max-side 256 --thresholds 41 --bootstrap 5000
if errorlevel 1 exit /b 1

echo.
echo STAGE 12B COMPLETE.
echo Please send:
echo   results\local_dev\stage12b_fuzzy_signature\summary.json
echo   results\local_dev\stage12b_fuzzy_signature\selection_ranking.csv
echo   results\local_dev\stage12b_fuzzy_signature\heldout_top7.csv
echo   results\local_dev\stage12b_fuzzy_signature\evidence_banks.json
echo   results\local_dev\stage12b_fuzzy_signature\winner_preview.png
endlocal
