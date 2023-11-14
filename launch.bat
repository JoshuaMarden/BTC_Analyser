@echo off

REM Change to the directory where the setup.bat script is located
cd %~dp0

REM Set the virtual environment directory
SET VENV_DIR=btc_analyser_venv

REM Check if the virtual environment directory exists
IF NOT EXIST "%VENV_DIR%" (
    REM Call the setup script if the venv doesn't exist
    echo Virtual environment not found. Setting up...
    CALL setup.bat
)

REM Activate the virtual environment
CALL %VENV_DIR%\Scripts\activate.bat

REM Run the Python script in the scripts directory
py -3.11 "scripts\run.py"

REM Deactivate the virtual environment
CALL btc_analyser_venv\Scripts\deactivate.bat

pause