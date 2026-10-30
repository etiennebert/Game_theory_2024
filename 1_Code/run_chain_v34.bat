@echo off
rem  V34 chain, unattended: Calibrate_BAU_productivity.R -> Baseline_2stage.R -> Run_V34_all.R, each in its own Rscript process
rem  (run_step.R). Double-click this file, or in a terminal:  cd C:\runGTAP375\Game_theory_2024\1_Code  then  run_chain_v34.bat
rem  Steps whose output exists are skipped (step 1: bau_afeall_eta0.66_v34.txt; step 2: B_eudr\NATDEF_B.sl4; step 3 reuses its own runs),
rem  so the chain can be relaunched after an interruption. Log of the steps: 3_Output\chain_v34_log.txt (the runs themselves log to
rem  3_Output\overnight_log.txt and 4_DB\V34_runs_<date>.txt). Keep the machine awake (power settings) - about 46 hours in all.
setlocal
cd /d "%~dp0"
where Rscript >nul 2>&1 && goto :found
rem  R is not on the PATH: ask the registry (the R installer writes InstallPath there), then the usual folders
for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\R-core\R" /v InstallPath 2^>nul ^| find "InstallPath"') do set "RHOME=%%b"
if not defined RHOME for /f "tokens=2,*" %%a in ('reg query "HKCU\SOFTWARE\R-core\R" /v InstallPath 2^>nul ^| find "InstallPath"') do set "RHOME=%%b"
if not defined RHOME for /d %%d in ("%ProgramFiles%\R\R-*" "%LOCALAPPDATA%\Programs\R\R-*" "%ProgramFiles(x86)%\R\R-*" "C:\R\R-*") do set "RHOME=%%~d"
if defined RHOME set "PATH=%PATH%;%RHOME%\bin"
where Rscript >nul 2>&1 || (echo Rscript not found. Find it with:  where /r "C:\Program Files" Rscript.exe   then run:  set "PATH=%%PATH%%;<that folder>"  and relaunch & pause & exit /b 1)
:found
for /f "delims=" %%r in ('where Rscript') do echo using %%r
set "LOG=..\3_Output\chain_v34_log.txt"
echo %date% %time% chain start >> "%LOG%"
if exist "..\0_External_data\DeDuCE_rework\bau_afeall_eta0.66_v34.txt" (
  echo %date% %time% SKIP Calibrate_BAU_productivity.R - bau_afeall_eta0.66_v34.txt exists >> "%LOG%"
) else (
  echo %date% %time% START Calibrate_BAU_productivity.R >> "%LOG%"
  Rscript run_step.R Calibrate_BAU_productivity.R || goto :fail
  echo %date% %time% DONE Calibrate_BAU_productivity.R >> "%LOG%"
)
if exist "..\3_Output\Baseline_2stage_bau5_eta0.66_v34\B_eudr\NATDEF_B.sl4" (
  echo %date% %time% SKIP Baseline_2stage.R - B_eudr\NATDEF_B.sl4 exists >> "%LOG%"
) else (
  echo %date% %time% START Baseline_2stage.R >> "%LOG%"
  Rscript run_step.R Baseline_2stage.R || goto :fail
  echo %date% %time% DONE Baseline_2stage.R >> "%LOG%"
)
echo %date% %time% START Run_V34_all.R >> "%LOG%"
Rscript run_step.R Run_V34_all.R || goto :fail
echo %date% %time% DONE Run_V34_all.R - chain finished >> "%LOG%"
echo chain finished
pause
exit /b 0
:fail
echo %date% %time% FAILED at the step above (see the terminal and 3_Output\overnight_log.txt) >> "%LOG%"
echo FAILED - see 3_Output\chain_v34_log.txt
pause
exit /b 1
