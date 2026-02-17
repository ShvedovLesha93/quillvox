import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
binaries = []

# Collect all data files
datas = []

# Collect data files from dependencies
try:
    datas += collect_data_files('faster_whisper', include_py_files=False)
except Exception:
    pass


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuillVox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='runtime',
    # icon='app/resources/icons/app_icon.ico',  # Uncomment and add your app icon
)

coll = COLLECT(
    exe,
    a.binaries,
    # a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuillVox',
)
