@echo off

echo Checking and setting up the virtual environment...
py -3.11 -m venv btc_analyser_venv

REM Change to the directory where the setup.bat script is located
cd %~dp0

echo Installing dependencies...
btc_analyser_venv\Scripts\pip install -r requirements.txt

echo Environment setup is complete.