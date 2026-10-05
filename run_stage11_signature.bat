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

echo [MFI-Edge] Stage 11 - Edge Signature Discovery
rem First campaign is intentionally analytical: discover and validate the
rem signature before spending time on the optional learned diagnostic upper bound.
python analyze_gt_edge_signatures.py --max-side 256 --max-samples-per-group 2500 --candidate-features 8 --max-abs-corr 0.92 --no-linear-diagnostic
if errorlevel 1 exit /b %errorlevel%

echo.
echo [MFI-Edge] Done. Send me:
echo   results\local_dev\edge_signature\SIGNATURE_REPORT.md
echo   results\local_dev\edge_signature\candidate_signature.json
echo   results\local_dev\edge_signature\diagnostic_results.json
echo   results\local_dev\edge_signature\descriptor_pairwise_summary.csv
echo and, if convenient, the three PNG diagnostics.
endlocal
