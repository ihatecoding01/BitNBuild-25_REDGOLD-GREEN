@echo off
echo ========================================
echo   Revuze Extension Setup
echo ========================================
echo.

echo Installing Python dependencies...
cd backend
pip install -r requirements.txt

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python backend/main.py (to start the backend server)
echo 2. Open Chrome and go to chrome://extensions/
echo 3. Enable "Developer mode" (top right)
echo 4. Click "Load unpacked" and select the "review_extension" folder
echo 5. Visit an Amazon product page and click the Revuze icon!
echo.
echo Backend will be running on: http://localhost:8000
echo.
pause