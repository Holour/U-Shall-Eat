# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE

# 设置 pathex 为当前目录的绝对路径
pathex = [os.path.abspath('.')]

# 收集 resources 目录下的所有数据文件
datas = collect_data_files('resources', include_py_files=False)

a = Analysis(
    ['main.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,  # 添加 resources 文件
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
    name='邮小食',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 如果需要调试，可以临时设置为 True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo_1.ico'
)
