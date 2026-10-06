@echo off
setlocal
cd /d %~dp0

echo ============================================================
echo MFI-Edge Stage 12c - leakage-free evidence-bank CV
echo ============================================================
echo.

python run_stage12c_leakfree_cv.py --max-side 256 --thresholds 41 --folds 3 --bootstrap 5000 --top-heldout 7
if errorlevel 1 (
  echo.
  echo STAGE 12c FAILED
  exit /b 1
)

echo.
echo STAGE 12c COMPLETE
echo Send these files:
echo   results\local_dev\stage12c_leakfree_cv\summary.json
echo   results\local_dev\stage12c_leakfree_cv\leakfree_selection_ranking.csv
echo   results\local_dev\stage12c_leakfree_cv\fold_results.csv
echo   results\local_dev\stage12c_leakfree_cv\bank_stability.csv
echo   results\local_dev\stage12c_leakfree_cv\heldout_top7.csv
echo   results\local_dev\stage12c_leakfree_cv\winner_preview.png
echo   results\local_dev\stage12c_leakfree_cv\best_dual_preview.png
endlocal
