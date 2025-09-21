# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all data files (images, sounds, etc.)
datas = []
datas += collect_data_files('pygame')

# Add game assets
assets_dirs = [
    'data',
    'assets', 
    'Background layers',
    'Futuristic City Parallax'
]

for asset_dir in assets_dirs:
    if os.path.exists(asset_dir):
        datas.append((asset_dir, asset_dir))

# Add JSON files that are needed
json_files = [
    'Daytime.json',
    'Legacy-Fantasy.json', 
    'NIght_time.json',
    'programmerArt_1.json',
    'Hearts.json',
    'hearts1.json',
    'forest2.json',
    'night_time_map.json',
    'game_settings.json',
    'story_progress.json'
]

for json_file in json_files:
    if os.path.exists(json_file):
        datas.append((json_file, '.'))

# Add image files
image_files = [
    'Character.png',
    'Arrow01(32x32).png',
    'Attack-01-Sheet.png',
    'Soldier-Attack01.png',
    'Soldier-Attack03.png', 
    'Soldier-Walk.png',
    'hearts_full.png',
    'hearts1.png',
    'programmerArt_1.png',
    'programmerArt_1-sheet.png',
    'spritesheet.png',
    'Tileset.png',
    'Tileset Outside.png'
]

for image_file in image_files:
    if os.path.exists(image_file):
        datas.append((image_file, '.'))

# Add map files
map_files = [
    'data/maps/0.json',
    'data/maps/1.json', 
    'data/maps/2.json'
]

for map_file in map_files:
    if os.path.exists(map_file):
        datas.append((map_file, 'data/maps'))

# Hidden imports
hiddenimports = [
    'pygame',
    'json',
    'os',
    'sys',
    'platform',
    'hashlib',
    'tempfile',
    'typing',
    'requests',
    'logging',
    'datetime',
    'random',
    'string',
    'math',
    'api_client'
]

# Exclude backend folder and unnecessary modules
excludes = [
    'backend',
    'test_*',
    'setup_backend',
    'flask',
    'pymongo',
    'dotenv',
    'bson'
]

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LunaEndlessLesson',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile=True,
    windowed=False
)
