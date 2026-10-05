@echo off
setlocal
cd /d %~dp0

set PRESET=%1
if "%PRESET%"=="" set PRESET=standard

if not exist .venv\Scripts\python.exe (
  echo [MFI-Edge] Creating Python virtual environment...
  py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1

echo.
echo [MFI-Edge] Running local CH-MFI preset: %PRESET%
echo [MFI-Edge] Results: results\local_dev\ch_mfi
echo.
python run_local_research.py --preset %PRESET% --profile-workers

endlocal
