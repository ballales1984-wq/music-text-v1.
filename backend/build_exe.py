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
    '--add-data=uploads;uploads',
    '--add-data=outputs;outputs',
    '--hidden-import=uvicorn',
    '--hidden-import=fastapi',
    '--hidden-import=whisper',
    '--hidden-import=openai',
    '--hidden-import=transformers',
    '--hidden-import=torch',
    '--hidden-import=torchaudio',
    '--hidden-import=librosa',
    '--hidden-import=scipy',
    '--hidden-import=numpy',
    '--hidden-import=crepe',
    '--hidden-import=noisereduce',
    '--hidden-import=pronouncing',
    '--hidden-import=text_structure',
    '--hidden-import=syllable_counter',
    '--hidden-import=text_cleaner',
    '--hidden-import=lyrics_generator',
    '--hidden-import=lyrics_generator_simple',
    '--hidden-import=transcription',
    '--hidden-import=job_status_redis',
    '--hidden-import=redis',
    '--hidden-import=redis.client',
    '--hidden-import=redis.connection',
    '--hidden-import=separation',
    '--hidden-import=memory_manager',
    '--hidden-import=song_patterns_analyzer',
    '--hidden-import=timing_analysis',
    '--hidden-import=grammar_corrector',
    '--hidden-import=audio_analysis',
    '--hidden-import=audio_chunking',
    '--hidden-import=audio_structure_analysis',
    '--hidden-import=metric_analysis',
    '--hidden-import=rhythmic_analysis',
    '--hidden-import=voice_segmentation',
    '--hidden-import=pydantic',
    '--hidden-import=requests',
    '--hidden-import=dotenv',
    '--hidden-import=pydub',
    '--hidden-import=soundfile',
    '--hidden-import=tqdm',
]

print("Creazione eseguibile in corso...")
print(f"Output: {dist_dir}")
PyInstaller.__main__.run(args)
print("Eseguibile creato!")
