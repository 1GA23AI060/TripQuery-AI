@echo off
echo ========================================================
echo ✈️ Launching TripQuery AI (Backend & Frontend)
echo ========================================================
start "TripQuery AI Backend" cmd /c "start_backend.bat"
timeout /t 3 /nobreak >nul
start "TripQuery AI Frontend" cmd /c "start_frontend.bat"
echo.
echo Backend URL:  http://localhost:8000
echo Frontend URL: http://localhost:5173
echo API Docs:     http://localhost:8000/docs
echo.
pause
