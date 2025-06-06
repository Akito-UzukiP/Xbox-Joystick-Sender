"""
Setup script for building Xbox Controller GUI executable
Uses PyInstaller to create a standalone executable
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['joystick_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('controller_config.json', '.'),
    ],
    hiddenimports=[
        'pygame.joystick',
        'pygame.mixer',
        'pygame.font',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Xbox_Controller_GUI',
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
    icon=None
)
"""
    
    with open('joystick_gui.spec', 'w') as f:
        f.write(spec_content.strip())
    print("Created joystick_gui.spec")

def main():
    """Main setup function"""
    print("Xbox Controller GUI Setup")
    print("=" * 30)
    
    # Create spec file
    create_spec_file()
    
    print("\nSetup complete!")
    print("\nTo build the executable:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Install PyInstaller: pip install pyinstaller")
    print("3. Build executable: pyinstaller joystick_gui.spec")
    print("\nThe executable will be created in the 'dist' folder.")

if __name__ == "__main__":
    main()
