# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Meeting Transcriber Pro
# Usage: pyinstaller MeetingTranscriber.spec

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# ---------------------------------------------------------------------------
# Collect data files for packages that need them at runtime
# ---------------------------------------------------------------------------
datas = []
binaries = []

# python-dotenv
dotenv_datas, dotenv_binaries, dotenv_hiddenimports = collect_all('dotenv')
datas += dotenv_datas
binaries += dotenv_binaries

# openai
openai_datas, openai_binaries, openai_hiddenimports = collect_all('openai')
datas += openai_datas
binaries += openai_binaries

# faster-whisper model support files
try:
    fw_datas, fw_binaries, fw_hiddenimports = collect_all('faster_whisper')
    datas += fw_datas
    binaries += fw_binaries
except Exception:
    fw_hiddenimports = []

# PySide6
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')
datas += pyside6_datas
binaries += pyside6_binaries

# sounddevice / soundcard
try:
    sd_datas, sd_binaries, sd_hiddenimports = collect_all('sounddevice')
    datas += sd_datas
    binaries += sd_binaries
except Exception:
    sd_hiddenimports = []

try:
    sc_datas, sc_binaries, sc_hiddenimports = collect_all('soundcard')
    datas += sc_datas
    binaries += sc_binaries
except Exception:
    sc_hiddenimports = []

# Include .env.example (template only) so the user has a reference in the install dir.
# NEVER include the real .env file – it contains API keys.
import os as _os
if _os.path.exists('.env'):
    _env_content = open('.env').read()
    if 'OPENAI_API_KEY' in _env_content and 'your_openai_api_key_here' not in _env_content:
        raise RuntimeError(
            "\n\n*** SECURITY ABORT ***\n"
            "A .env file with a real API key was detected in the project root.\n"
            "PyInstaller must NOT bundle it. The build has been stopped.\n"
            "This is expected – .env is intentionally excluded from the package.\n"
            "Do NOT add .env to the datas list.\n"
        )
datas += [('.env.example', '.')]

# ---------------------------------------------------------------------------
# Bundle FFmpeg binaries if present in the project root's "ffmpeg" folder.
# Place ffmpeg.exe and ffprobe.exe into:
#   <project_root>/ffmpeg/ffmpeg.exe
#   <project_root>/ffmpeg/ffprobe.exe
# before running PyInstaller so they get bundled automatically.
# ---------------------------------------------------------------------------
ffmpeg_dir = Path('ffmpeg')
if ffmpeg_dir.exists():
    for exe in ffmpeg_dir.glob('*.exe'):
        binaries += [(str(exe), 'ffmpeg')]

# ---------------------------------------------------------------------------
# Hidden imports that PyInstaller may miss
# ---------------------------------------------------------------------------
hidden_imports = [
    'dotenv',
    'openai',
    'openai._compat',
    'numpy',
    'sounddevice',
    'soundcard',
    'wave',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtMultimedia',
    'src',
    'src.config',
    'src.audio_capture',
    'src.transcription',
    'src.summarization',
    'src.file_manager',
    'src.ffmpeg_utils',
    'src.diarization',
    'src.gui_app',
]
hidden_imports += openai_hiddenimports
hidden_imports += fw_hiddenimports
hidden_imports += pyside6_hiddenimports
hidden_imports += sd_hiddenimports if 'sd_hiddenimports' in dir() else []
hidden_imports += sc_hiddenimports if 'sc_hiddenimports' in dir() else []

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ['src/gui_app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# EXE (the launcher inside the bundle directory)
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MeetingTranscriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='installer/icon.ico',   # Uncomment and supply an .ico file if desired
)

# ---------------------------------------------------------------------------
# COLLECT – one-folder mode (required for WiX packaging)
# ---------------------------------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MeetingTranscriber',
)
