"""
Script per creare eseguibile del backend con PyInstaller
"""
import PyInstaller.__main__
import sys
from pathlib import Path

# Paths
backend_dir = Path(__file__).parent
main_file = backend_dir / "main_simple.py"
dist_dir = backend_dir / "dist"
build_dir = backend_dir / "build"

# Opzioni PyInstaller
args = [
    str(main_file),
    '--name=music-text-generator-backend',
    '--onefile',
    '--windowed',  # No console window
    '--clean',
    f'--distpath={dist_dir}',
    f'--workpath={build_dir}',
    '--add-data=uploads;uploads',  # Include uploads directory
    '--hidden-import=uvicorn',
    '--hidden-import=fastapi',
    '--hidden-import=whisper',
    '--hidden-import=openai',
    '--hidden-import=transformers',
    '--hidden-import=torch',
    '--hidden-import=torchaudio',
    '--hidden-import=librosa',
    '--hidden-import=spleeter',
    '--hidden-import=pronouncing',
    '--hidden-import=text_structure',
    '--hidden-import=syllable_counter',
    '--hidden-import=text_cleaner',
    '--hidden-import=lyrics_generator',
    '--hidden-import=transcription',
]

print("Creazione eseguibile in corso...")
print(f"Output: {dist_dir}")
PyInstaller.__main__.run(args)
print("Eseguibile creato!")

