@echo off
rem  27 Oct 2026: the switching-cost bracket at 1 % of trade (EU alone, flat penalty and footprint surcharge), run unattended with
rem  Rscript. Double-click this file, or in a terminal:  cd C:\runGTAP375\Game_theory_2024\1_Code  then  run_brackets_1pct.bat
rem  It runs Run_V34_all.R with FOREST_CLUB_BLOCKS=brackets: the 0.05 % and 0.2 % brackets are reused from their csv, the 1 %
rem  runs (brackets_def, fr = 0.01) are solved, 4-6 runs of up to 15 solves. Log: 3_Output\overnight_log.txt and
rem  4_DB\V34_runs_<date>.txt. Then:  python ..\5_Figures\make_all.py  redraws Extended Data Fig. 1 and Table 3 with the new rows.
setlocal
cd /d "%~dp0"
where Rscript >nul 2>&1 && goto :found
for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\R-core\R" /v InstallPath 2^>nul ^| find "InstallPath"') do set "RHOME=%%b"
if not defined RHOME for /f "tokens=2,*" %%a in ('reg query "HKCU\SOFTWARE\R-core\R" /v InstallPath 2^>nul ^| find "InstallPath"') do set "RHOME=%%b"
if not defined RHOME for /d %%d in ("%ProgramFiles%\R\R-*" "%LOCALAPPDATA%\Programs\R\R-*" "%ProgramFiles(x86)%\R\R-*" "C:\R\R-*") do set "RHOME=%%~d"
if defined RHOME set "PATH=%PATH%;%RHOME%\bin"
where Rscript >nul 2>&1 || (echo Rscript not found. Find it with:  where /r "C:\Program Files" Rscript.exe   then run:  set "PATH=%%PATH%%;<that folder>"  and relaunch & pause & exit /b 1)
:found
for /f "delims=" %%r in ('where Rscript') do echo using %%r
set "FOREST_CLUB_BLOCKS=brackets"
echo %date% %time% brackets 1 pct start >> "..\3_Output\chain_v34_log.txt"
Rscript run_step.R Run_V34_all.R || (echo %date% %time% brackets 1 pct FAILED >> "..\3_Output\chain_v34_log.txt" & pause & exit /b 1)
echo %date% %time% brackets 1 pct done >> "..\3_Output\chain_v34_log.txt"
pause
