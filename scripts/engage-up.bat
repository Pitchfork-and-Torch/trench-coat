@echo off
cd /d "%~dp0\.."
".venv\Scripts\python.exe" -m trenchcoat up --accept-legal --wait-tor 90 --chain casual-shadow
