@echo off
echo Starting RAGIT Frontend...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting the application...
echo Open your browser and navigate to: http://localhost:8086
echo.
echo Demo Accounts:
echo Admin: admin@ragagent.com / admin123
echo User:  user@ragagent.com / user123
echo.
echo Press Ctrl+C to stop the server
echo.
python main.py