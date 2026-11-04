@echo off
chcp 65001 > nul
echo ========================================================
echo   AssetFlow v2.1 - Portfolio ^& Asset Allocation Server
echo ========================================================
echo.
echo Starting FastAPI server at http://localhost:8000 ...
echo Opening dashboard in default browser...
echo Press Ctrl+C to stop.
echo.

cd /d "%~dp0"
call .venv\Scripts\activate
start http://localhost:8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
