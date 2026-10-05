@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo [MFI-Edge] Creating .venv...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%

echo [MFI-Edge] Stage 12a - fixed Scharr + scale-relational signature gate
python run_stage12_signature_gate.py --max-side 256 --thresholds 41 --max-features 10 --max-abs-corr 0.88 --bootstrap 5000
if errorlevel 1 exit /b %errorlevel%

echo.
echo [MFI-Edge] Done. Send me:
echo   results\local_dev\stage12_signature_gate\summary.json
echo   results\local_dev\stage12_signature_gate\selection_ranking.csv
echo   results\local_dev\stage12_signature_gate\heldout_top5.csv
echo   results\local_dev\stage12_signature_gate\context_signature.json
echo   results\local_dev\stage12_signature_gate\winner_preview.png
endlocal
