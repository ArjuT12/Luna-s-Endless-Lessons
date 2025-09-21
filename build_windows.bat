@echo off
echo Building Luna's Endless Lesson for Windows...
echo.

REM Install requirements
pip install -r requirements_build.txt

REM Run the build script
python build.py

echo.
echo Build complete! Check for LunaEndlessLesson.exe
pause
