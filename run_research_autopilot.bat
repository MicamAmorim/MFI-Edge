@echo off
setlocal
cd /d %~dp0

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not defined MFI_CODEX_MODEL set MFI_CODEX_MODEL=gpt-5.6-sol

echo ============================================================
echo MFI-Edge Research Autopilot v4
echo Continuous autonomous non-neural SOTA research
echo Model: %MFI_CODEX_MODEL%
echo Normal decisions: medium reasoning
echo Research checkpoints: high reasoning + live web search
echo Persistent scientific context is injected on every decision.
echo Soft scientific stops automatically escalate to literature research.
echo Completed experiments are resumed safely if Codex analysis fails.
echo Create automation\STOP at any time to stop before the next step.
echo ============================================================
echo.

where git >nul 2>nul || (
  echo ERROR: git not found in PATH.
  exit /b 1
)
where python >nul 2>nul || (
  echo ERROR: python not found in PATH.
  exit /b 1
)
where codex >nul 2>nul || (
  echo ERROR: Codex CLI not found in PATH.
  echo Install/login and confirm: codex --version
  exit /b 1
)

python automation\research_controller_v4.py %*
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo.
  echo AUTOPILOT STOPPED WITH ERROR %RC%
  echo Check automation\runtime\ for logs/state.
  exit /b %RC%
)

echo.
echo AUTOPILOT FINISHED SAFELY
endlocal
