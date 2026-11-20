# -*- mode: python ; coding: utf-8 -*-

import sys

from PyInstaller.utils.hooks import collect_data_files

# Dash component libraries read package-info.json and serve their JS/CSS
# bundles from the installed package directory, so the data files have to
# be shipped alongside the Python modules.
datas = []
for package in [
    'dash',
    'dash_ag_grid',
    'dash_daq',
    'dash_bootstrap_components',
    'plotly',
]:
    datas += collect_data_files(package)

# The window icon is loaded at runtime from the package's assets folder.
datas += [('src/MNeuEventGUI/assets/icon.png', 'MNeuEventGUI/assets')]

# macOS needs an .icns icon; Windows uses the .ico. Linux ignores the icon.
icon = 'extras/icon.icns' if sys.platform == 'darwin' else 'extras/icon.ico'

a = Analysis(
    ['src/MNeuEventGUI/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name='MNeuEventGUI',
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
    icon=icon,
)
