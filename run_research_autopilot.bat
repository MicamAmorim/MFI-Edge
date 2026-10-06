@echo off
setlocal
cd /d %~dp0

echo ============================================================
echo MFI-Edge Research Autopilot
echo Local experiments + on-demand Codex decisions

echo Codex is NOT kept running while benchmarks execute.
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

python automation\research_controller.py %*
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
