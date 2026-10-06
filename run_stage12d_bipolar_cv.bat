@echo off
setlocal
cd /d %~dp0

echo ============================================================
echo MFI-Edge Stage 12d - repeated leakage-free bipolar CV
echo ============================================================
echo.
echo IMPORTANT: this stage does NOT inspect the old UDED held-out split.
echo.

python run_stage12d_bipolar_cv.py --max-side 256 --thresholds 41 --folds 3 --repeats 5
if errorlevel 1 (
  echo.
  echo STAGE 12d FAILED
  exit /b 1
)

echo.
echo STAGE 12d COMPLETE
echo Send these files:
echo   results\local_dev\stage12d_bipolar_cv\summary.json
echo   results\local_dev\stage12d_bipolar_cv\repeated_cv_ranking.csv
echo   results\local_dev\stage12d_bipolar_cv\family_summary.csv
echo   results\local_dev\stage12d_bipolar_cv\bank_stability.csv
echo   results\local_dev\stage12d_bipolar_cv\frozen_candidates.json
echo   results\local_dev\stage12d_bipolar_cv\selection_winner_preview.png
endlocal
