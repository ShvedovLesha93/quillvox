from PyInstaller.utils.hooks import collect_all

rich_datas, rich_binaries, rich_hiddenimports = collect_all("rich")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=rich_binaries,
    datas=rich_datas,
    hiddenimports=rich_hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="QuillVox",
    debug=False,
    console=True,
    onefile=True,
)
