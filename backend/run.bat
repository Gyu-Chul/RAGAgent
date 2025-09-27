@echo off
echo Starting RAG Agent Backend...
cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting backend server on port 9000...
uvicorn main:app --host 0.0.0.0 --port 9000 --reload

pause