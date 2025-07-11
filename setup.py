"""
Setup script for building Xbox Controller GUI executable - PyQt6 Version
Uses PyInstaller to create a standalone executable with PyQt6 support
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_spec_file():
    """Create PyInstaller spec file for PyQt6"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['joystick_gui_pyqt.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('controller_config.json', '.'),
    ],
    hiddenimports=[
        'pygame.joystick',
        'pygame.mixer',
        'pygame.font',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.sip',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'matplotlib.backends._backend_agg',
        'numpy',
        'controller_visualization',
        'message_bus_visualization',
        'plotting_visualization'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog'
    ],
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
    
    with open('joystick_gui_pyqt.spec', 'w') as f:
        f.write(spec_content.strip())
    print("Created joystick_gui_pyqt.spec for PyQt6")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('pygame', 'pygame'),
        ('matplotlib', 'matplotlib'),
        ('numpy', 'numpy')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"✗ {package_name} is missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print("pip install -r requirements_pyqt.txt")
        return False
    
    return True

def create_requirements_file():
    """Create updated requirements file for PyQt5"""
    requirements_content = """PyQt5>=5.15.0
pygame>=2.0.0
matplotlib>=3.5.0
numpy>=1.20.0
pyinstaller>=5.0.0
"""
    
    with open('requirements_pyqt.txt', 'w') as f:
        f.write(requirements_content.strip())
    print("Updated requirements_pyqt.txt")

def main():
    """Main setup function"""
    print("Xbox Controller GUI Setup - PyQt6 Version")
    print("=" * 50)
    
    # Create updated requirements file
    create_requirements_file()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Create spec file
    create_spec_file()
    
    print("\nSetup complete!")
    print("\nNext steps:")
    
    if not deps_ok:
        print("1. Install requirements: pip install -r requirements_pyqt6.txt")
        print("2. After installation, run this setup again to verify")
    else:
        print("1. All dependencies are installed ✓")
    
    print("2. Build executable: pyinstaller joystick_gui_pyqt.spec")
    print("3. The executable will be created in the 'dist' folder")
    
    print("\nNote: This setup is configured for PyQt6.")
    print("If you need to use PyQt5, please use the legacy setup.")
    
    print("\nTo run the application directly:")
    print("python joystick_gui_pyqt.py")

if __name__ == "__main__":
    main()
