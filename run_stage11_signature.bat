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

echo [MFI-Edge] Stage 11b - audit historical multiscale collapse
python audit_multiscale_features.py --max-side 256
if errorlevel 1 exit /b %errorlevel%

echo.
echo [MFI-Edge] Stage 11b - Edge Signature Discovery with oriented_ms
python analyze_gt_edge_signatures_ms.py --max-side 256 --max-samples-per-group 2500 --candidate-features 8 --max-abs-corr 0.90
if errorlevel 1 exit /b %errorlevel%

echo.
echo [MFI-Edge] Done. Send me:
echo   results\local_dev\edge_signature_ms\SCALE_AUDIT.md
echo   results\local_dev\edge_signature_ms\SIGNATURE_REPORT.md
echo   results\local_dev\edge_signature_ms\candidate_signature.json
echo   results\local_dev\edge_signature_ms\diagnostic_results.json
echo   results\local_dev\edge_signature_ms\descriptor_pairwise_summary.csv
echo and, if convenient, the three PNG diagnostics.
endlocal
