#!/bin/bash
echo "Building Luna's Endless Lesson for macOS..."
echo

# Install requirements
pip3 install -r requirements_build.txt

# Run the build script
python3 build.py

echo
echo "Build complete! Check for LunaEndlessLesson executable"
