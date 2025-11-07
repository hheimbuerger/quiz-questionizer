@echo off
echo Quiz Questionizer - Camera Testing Utility
echo.
echo This will help you find and test your cameras
echo.

echo 1. Discovering available cameras...
python app.py --discover

echo.
echo 2. If you found cameras above, you can test them individually:
echo    python app.py --camera 0 --test
echo    python app.py --camera 1 --test
echo    etc.
echo.
echo 3. For live preview:
echo    python app.py --camera 0 --preview
echo.
pause