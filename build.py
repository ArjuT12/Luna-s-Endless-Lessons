#!/usr/bin/env python3
"""
Build script for Luna's Endless Lesson
Creates executables for Windows, Linux, and macOS
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        return run_command("pip install pyinstaller", "Installing PyInstaller")

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def create_hidden_config():
    """Create hidden configuration files that players can't easily edit"""
    print("🔒 Setting up hidden configuration files...")
    
    # Make story_progress.json hidden and read-only
    if os.path.exists('story_progress.json'):
        if platform.system() == 'Windows':
            # On Windows, make file hidden and read-only
            os.system('attrib +h +r story_progress.json')
        else:
            # On Unix-like systems, make file hidden and read-only
            os.chmod('story_progress.json', 0o444)  # Read-only
    
    # Make game_settings.json hidden and read-only
    if os.path.exists('game_settings.json'):
        if platform.system() == 'Windows':
            os.system('attrib +h +r game_settings.json')
        else:
            os.chmod('game_settings.json', 0o444)

def build_executable():
    """Build the executable using PyInstaller"""
    current_platform = platform.system().lower()
    
    print(f"\n🏗️  Building for {current_platform.upper()}...")
    
    # Base PyInstaller command (spec file already contains all options)
    cmd = "pyinstaller --clean luna_game.spec"
    
    # Determine executable name based on platform
    if current_platform == "windows":
        exe_name = "LunaEndlessLesson.exe"
    else:  # macOS and Linux
        exe_name = "LunaEndlessLesson"
    
    success = run_command(cmd, f"Building {current_platform} executable")
    
    if success:
        # Move executable to root directory
        exe_path = os.path.join('dist', exe_name)
        if os.path.exists(exe_path):
            shutil.move(exe_path, exe_name)
            print(f"✅ Executable created: {exe_name}")
            
            # Make executable on Unix-like systems
            if current_platform != "windows":
                os.chmod(exe_name, 0o755)
        
        return True
    return False

def create_launcher_script():
    """Create a launcher script for easier distribution"""
    current_platform = platform.system().lower()
    
    if current_platform == "windows":
        launcher_content = '''@echo off
echo Starting Luna's Endless Lesson...
LunaEndlessLesson.exe
pause
'''
        with open('run_game.bat', 'w') as f:
            f.write(launcher_content)
        print("✅ Created run_game.bat launcher")
    
    elif current_platform == "darwin":  # macOS
        launcher_content = '''#!/bin/bash
echo "Starting Luna's Endless Lesson..."
./LunaEndlessLesson
'''
        with open('run_game.sh', 'w') as f:
            f.write(launcher_content)
        os.chmod('run_game.sh', 0o755)
        print("✅ Created run_game.sh launcher")
    
    else:  # Linux
        launcher_content = '''#!/bin/bash
echo "Starting Luna's Endless Lesson..."
./LunaEndlessLesson
'''
        with open('run_game.sh', 'w') as f:
            f.write(launcher_content)
        os.chmod('run_game.sh', 0o755)
        print("✅ Created run_game.sh launcher")

def create_readme():
    """Create a README for the built game"""
    readme_content = '''# Luna's Endless Lesson

## How to Run

### Windows
Double-click `run_game.bat` or `LunaEndlessLesson.exe`

### macOS/Linux
Run `./run_game.sh` or `./LunaEndlessLesson` in terminal

## Game Controls

- Arrow Keys: Move left/right
- Space: Jump
- F: Attack
- E: Switch weapons (when unlocked)
- I: Open inventory (when unlocked)
- W: Use selected item
- 1-5: Select inventory slots
- U: Close inventory
- R: Restart (when game over)
- Escape: Quit

## Story Progression

The game features a story progression system that unlocks new features as you play. Die to progress the story and unlock new abilities!

## Troubleshooting

If the game doesn't start:
1. Make sure you have the required system libraries
2. Try running from command line to see error messages
3. Check that all game files are present

Enjoy the game!
'''
    
    with open('README.txt', 'w') as f:
        f.write(readme_content)
    print("✅ Created README.txt")

def main():
    """Main build process"""
    print("🎮 Luna's Endless Lesson - Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ Error: main.py not found. Please run this script from the game directory.")
        sys.exit(1)
    
    # Install PyInstaller
    if not install_pyinstaller():
        print("❌ Failed to install PyInstaller")
        sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Set up hidden configuration
    create_hidden_config()
    
    # Build executable
    if not build_executable():
        print("❌ Build failed")
        sys.exit(1)
    
    # Create launcher script
    create_launcher_script()
    
    # Create README
    create_readme()
    
    print("\n🎉 Build completed successfully!")
    print("\nFiles created:")
    current_platform = platform.system().lower()
    
    if current_platform == "windows":
        print("- LunaEndlessLesson.exe (main executable)")
        print("- run_game.bat (launcher script)")
    else:
        print("- LunaEndlessLesson (main executable)")
        print("- run_game.sh (launcher script)")
    
    print("- README.txt (instructions)")
    print("\nThe backend folder is excluded, but API client is included for online backend.")
    print("Configuration files are hidden from players.")
    print("Players can run the game using the launcher script or executable directly.")

if __name__ == "__main__":
    main()
