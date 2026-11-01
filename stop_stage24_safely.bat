@echo off
setlocal
cd /d %~dp0
if not exist automation mkdir automation
type nul > automation\STOP_STAGE24
echo Safe-stop requested. Stage 24 will stop at the next checkpoint boundary.
endlocal
