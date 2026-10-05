@echo off
setlocal
cd /d %~dp0

set MODE=%1
if "%MODE%"=="" set MODE=quick
set WORKERS=%2
if "%WORKERS%"=="" set WORKERS=8

if not exist .venv\Scripts\python.exe py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt

set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1

echo ============================================================
echo MFI-Edge CH-MFI-v2 local research campaign
echo Mode: %MODE%   Workers: %WORKERS%
echo ============================================================

python smoke_local_architecture_v2.py
if errorlevel 1 exit /b %errorlevel%

if /I "%MODE%"=="smoke" goto :done

echo [1] Baseline v2 standard screen...
python run_local_research_v2.py --preset standard --workers %WORKERS% --profile-workers --out results\local_dev\ch_mfi_v2
if errorlevel 1 exit /b %errorlevel%

if /I "%MODE%"=="quick" goto :done

echo [2] Learning scale-specific capacity bank...
python learn_scale_capacity_bank.py --max-side 256
if errorlevel 1 exit /b %errorlevel%

echo [3] Learning exact regime-specific Shapley values...
python learn_regime_shapley.py --regimes all --target final --workers %WORKERS%
if errorlevel 1 exit /b %errorlevel%

set MFI_REGIME_SHAPLEY=results\local_dev\regime_shapley.json
set MFI_SCALE_CAPACITY_BANK=results\local_dev\scale_capacity_bank.json

echo [4] Extending standard competition with learned regime/scale models...
python run_local_research_v2.py --preset standard --workers %WORKERS% --profile-workers --out results\local_dev\ch_mfi_v2
if errorlevel 1 exit /b %errorlevel%

echo [5] Topology competition for selection-ranked finalists...
python benchmark_topology_v2.py --ranking results\local_dev\ch_mfi_v2\selection_ranking.csv --preset standard --top 8 --bootstrap 5000
if errorlevel 1 exit /b %errorlevel%

if /I "%MODE%"=="full" goto :done
if /I "%MODE%"=="wide" (
  echo [6] Wide overnight exploration...
  python run_local_research_v2.py --preset wide --workers %WORKERS% --out results\local_dev\ch_mfi_v2_wide
  if errorlevel 1 exit /b %errorlevel%
)

:done
echo.
echo ============================================================
echo Campaign stage complete.
echo See results\local_dev\ and docs\paper\
echo ============================================================
endlocal
