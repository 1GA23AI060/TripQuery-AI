@echo off
echo Starting TripQuery AI Backend...
cd backend
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
python run.py
pause
