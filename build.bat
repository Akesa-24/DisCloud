@echo off
REM builds dist\DisCloud.exe
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name DisCloud --icon icon.ico --add-data "icon.ico;." main.py
echo.
echo Done, DisCloud.exe is in the dist folder
pause
