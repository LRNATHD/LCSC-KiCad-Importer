@echo off
echo Installing requirements...
python -m pip install -r requirements.txt

echo.
echo Building LCSC Importer Executable...
python -m PyInstaller --noconfirm --onefile --copy-metadata JLC2KiCadLib --icon "icon.ico" --add-data "icon.png;." --name "LCSC_Importer"  "main.py"

echo.
echo Copying config.ini to dist folder...
copy /Y "config.ini" "dist\config.ini" >nul 2>&1

echo.
echo Build complete! The executable is located in the 'dist' folder.
pause
