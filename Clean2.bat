@echo off
REM  run_clean2.bat — auto-download and run Clean2.py from GitHub

SET "URL=https://raw.githubusercontent.com/vimalisgoodboy/kali/refs/heads/main/Clean2.py"
SET "SCRIPT=Clean2.py"

echo Downloading Clean2.py from GitHub...

powershell -Command "try {Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -OutFile '%SCRIPT%'} catch {exit 1}}"
IF NOT EXIST "%SCRIPT%" (
    echo Failed to download Clean2.py. Exiting.
    pause
    exit /b 1
)

REM Check for python or python3
where python >nul 2>&1
IF ERRORLEVEL 1 (
   where python3 >nul 2>&1
   IF ERRORLEVEL 1 (
       echo Python not found. Please install Python and ensure it's in your PATH.
       pause
       exit /b 1
   ) ELSE (
       SET "PY=python3"
   )
) ELSE (
   SET "PY=python"
)

echo Running Clean2.py (this will wipe all Chrome & Edge data)...
%PY% "%SCRIPT%"

echo Cleaning is complete.
pause
