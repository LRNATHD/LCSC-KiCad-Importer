@echo off
echo Installing requirements...
python -m pip install -r requirements.txt

echo.
echo Building LCSC Importer Executable...
python -m PyInstaller --noconfirm --onefile --windowed --copy-metadata JLC2KiCadLib --icon "icon.ico" --add-data "icon.png;." --name "LCSC_Importer"  "main.py"

echo.
echo Build complete! The executable is located in the 'dist' folder.
pause
