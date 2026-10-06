@echo off
setlocal
cd /d %~dp0

echo ============================================================
echo MFI-Edge Stage 13a - frozen external BSDS500 transfer

echo IMPORTANT: this runs the frozen Stage-12d representatives.
echo No BSDS labels are used to tune feature banks, hyperparameters, or frozen thresholds.
echo The reported BSDS metrics are a tolerant-consensus proxy, not the official Berkeley matcher.
echo ============================================================
echo.

python run_stage13_bsds_transfer.py --split test --max-side 256 --thresholds 61 --bootstrap 5000 %*
if errorlevel 1 (
  echo.
  echo STAGE 13a FAILED
  exit /b 1
)

echo.
echo STAGE 13a COMPLETE
echo Send these files:
echo   results\external\stage13a_bsds_transfer\summary.json
echo   results\external\stage13a_bsds_transfer\external_metrics.csv
echo   results\external\stage13a_bsds_transfer\per_image_metrics.csv
echo   results\external\stage13a_bsds_transfer\preview_positive_control.png
echo   results\external\stage13a_bsds_transfer\preview_separable_bicapacity.png
echo   results\external\stage13a_bsds_transfer\preview_ratio_control.png
endlocal
