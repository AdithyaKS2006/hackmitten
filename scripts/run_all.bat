@echo off
echo Starting AO-03 Root Cause Evidence Engine...

REM Check venv
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Load scenarios
python scripts\load_to_mongo.py

REM Start backend
start "AO-03 Backend API" python manage.py runserver 8000

REM Start frontend
cd frontend
if not exist node_modules (
    npm install
)
start "AO-03 Frontend UI" npm run dev
cd ..

echo System running at http://localhost:8000 and http://localhost:5173
pause
