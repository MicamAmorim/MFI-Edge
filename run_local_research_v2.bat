@echo off
setlocal
cd /d %~dp0

set PRESET=%1
if "%PRESET%"=="" set PRESET=standard
set WORKERS=%2
if "%WORKERS%"=="" set WORKERS=8

if not exist .venv\Scripts\python.exe (
  echo [MFI-Edge] Creating Python virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt

set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1

echo [MFI-Edge] Running CH-MFI-v2 smoke test...
python smoke_local_architecture_v2.py
if errorlevel 1 exit /b %errorlevel%

if exist results\local_dev\regime_shapley.json set MFI_REGIME_SHAPLEY=results\local_dev\regime_shapley.json
if exist results\local_dev\scale_capacity_bank.json set MFI_SCALE_CAPACITY_BANK=results\local_dev\scale_capacity_bank.json

echo.
echo [MFI-Edge] CH-MFI-v2 preset=%PRESET% workers=%WORKERS%
echo [MFI-Edge] Output: results\local_dev\ch_mfi_v2
echo.
python run_local_research_v2.py --preset %PRESET% --workers %WORKERS% --profile-workers --out results\local_dev\ch_mfi_v2

endlocal
