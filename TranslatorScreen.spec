# TranslatorScreen.spec
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect mediapipe data files (face mesh models, etc.)
mediapipe_datas = collect_data_files("mediapipe")

a = Analysis(
    ["main.py"],
    pathex=[os.getcwd()],
    binaries=[],
    datas=mediapipe_datas,
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "PIL._tkinter_finder",
        "easyocr",
        "easyocr.detection",
        "easyocr.recognition",
        "easyocr.utils",
        "mediapipe",
        "cv2",
        "mss",
        "mss.windows",
        "pytesseract",
        "deep_translator",
        "deep_translator.google",
        "pykakasi",
        "pypinyin",
        "hangul_romanize",
        "hangul_romanize.rule",
        "scipy.special._ufuncs_cxx",
        "scipy.linalg.cython_blas",
        "scipy.linalg.cython_lapack",
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
    [],
    exclude_binaries=True,
    name="TranslatorScreen",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TranslatorScreen",
)
