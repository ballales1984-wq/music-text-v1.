"""
Script per creare eseguibile .exe dell'applicazione
Usa PyInstaller per creare un file standalone
"""
import os
import sys
import subprocess
from pathlib import Path

def build_exe():
    """Crea eseguibile .exe per backend e frontend."""
    
    print("=" * 60)
    print("BUILD ESECUIBILE .EXE")
    print("=" * 60)
    
    # Verifica PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller disponibile")
    except ImportError:
        print("📦 Installazione PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    backend_dir = Path("backend")
    frontend_dir = Path("frontend")
    
    # Build Backend
    print("\n🔨 Building Backend...")
    os.chdir(backend_dir)
    
    # Crea spec file per backend
    backend_spec = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'whisper',
        'librosa',
        'torch',
        'torchaudio',
        'numpy',
        'soundfile',
        'transformers',
        'requests',
        'openai'
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
    name='MusicTextGenerator_Backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    with open("backend.spec", "w") as f:
        f.write(backend_spec)
    
    # Build
    subprocess.run([sys.executable, "-m", "PyInstaller", "backend.spec", "--clean"], check=True)
    
    os.chdir("..")
    
    print("✅ Backend .exe creato in backend/dist/")
    
    # Frontend: usa electron-builder o simile
    print("\n📝 Nota: Frontend richiede Node.js, usa 'npm run build' per produzione")
    print("   Per .exe frontend, considera Electron o Tauri")
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETATO!")
    print("=" * 60)
    print("\nFile creati:")
    print("  - backend/dist/MusicTextGenerator_Backend.exe")
    print("\nPer avviare:")
    print("  - Esegui MusicTextGenerator_Backend.exe")
    print("  - Apri http://localhost:8000 nel browser")

if __name__ == "__main__":
    build_exe()

