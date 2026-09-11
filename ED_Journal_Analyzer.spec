# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect hidden imports and static datas
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'webview.platforms.winforms',
    'clr',
    'sqlite3',
    'psutil',
    'app.analyzer.stellar_physics',
    'app.services.physics_translator',
] + collect_submodules('uvicorn') + collect_submodules('fastapi') + collect_submodules('webview') + collect_submodules('psutil') + collect_submodules('app')

datas = [
    ('app/ui', 'app/ui'),
    ('app/data', 'app/data'),
    ('app/icon.ico', 'app'),
] + collect_data_files('webview')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['notebook', 'jupyter', 'IPython', 'pytest'],
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
    name='ED_Journal_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide command prompt window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/icon.ico',
)
