@echo off
REM FPL Pipeline Orchestrator Batch Wrapper
REM This file runs the Python orchestrator and is called by Windows Task Scheduler

setlocal enabledelayedexpansion

REM Set paths
set SCRIPT_PATH=C:\Users\JesseOnu\fpl sql rework\orchestrator\fpl_pipeline_orchestrator.py
set PYTHON_PATH=C:\ProgramData\anaconda3\python.exe
set LOG_FILE=C:\Users\JesseOnu\fpl sql rework\logs\pipeline_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%.log

REM Create logs directory if it doesn't exist
if not exist "C:\Users\JesseOnu\fpl sql rework\logs" mkdir "C:\Users\JesseOnu\fpl sql rework\logs"

REM Run Python orchestrator
echo [%date% %time%] Starting FPL Pipeline Orchestrator >> "%LOG_FILE%"
"%PYTHON_PATH%" "%SCRIPT_PATH%" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% equ 0 (
    echo [%date% %time%] Pipeline completed successfully >> "%LOG_FILE%"
) else (
    echo [%date% %time%] Pipeline failed with error code %ERRORLEVEL% >> "%LOG_FILE%"
)

endlocal