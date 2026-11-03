@echo off
cd /d "%~dp0"
if not exist "automation" mkdir "automation"
type nul > "automation\STOP_STAGE24_PAPER_A"
echo Safe-stop marker created. Current group may complete before the campaign exits.
echo To resume: del automation\STOP_STAGE24_PAPER_A
