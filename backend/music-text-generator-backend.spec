# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['d:\\music text\\backend\\main_simple.py'],
    pathex=[],
    binaries=[],
    datas=[('uploads', 'uploads'), ('outputs', 'outputs')],
    hiddenimports=['uvicorn', 'fastapi', 'whisper', 'openai', 'transformers', 'torch', 'torchaudio', 'librosa', 'scipy', 'numpy', 'crepe', 'noisereduce', 'pronouncing', 'text_structure', 'syllable_counter', 'text_cleaner', 'lyrics_generator', 'lyrics_generator_simple', 'transcription', 'job_status_redis', 'redis', 'redis.client', 'redis.connection', 'separation', 'memory_manager', 'song_patterns_analyzer', 'timing_analysis', 'grammar_corrector', 'audio_analysis', 'audio_chunking', 'audio_structure_analysis', 'metric_analysis', 'rhythmic_analysis', 'voice_segmentation', 'pydantic', 'requests', 'dotenv', 'pydub', 'soundfile', 'tqdm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='music-text-generator-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
