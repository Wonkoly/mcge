# -*- mode: python ; coding: utf-8 -*-
# Empaquetado en modo --onedir (NO --onefile): onefile descomprime todo a
# %TEMP% en cada arranque, que es de donde viene la sensación de lentitud
# al abrir la app. onedir arranca directo desde la carpeta ya extraída.
#
# Construir (en Windows, PyInstaller no cruza de plataforma):
#   pyinstaller mcg.spec
# Resultado: dist/MaestriaGeofisica/MaestriaGeofisica.exe + carpeta con
# dependencias — copiar la carpeta COMPLETA a la PC de destino, no solo el
# .exe.

datas = [
    ("app/web/templates", "app/web/templates"),
    ("app/web/static", "app/web/static"),
    ("app/documents/templates_docx", "app/documents/templates_docx"),
    ("app/documents/assets", "app/documents/assets"),
]

hiddenimports = [
    "docxtpl",
    "docx",
    "jinja2.ext",
    "sqlalchemy.dialects.sqlite",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="MaestriaGeofisica",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # deja ver la URL/errores en una consola; cambiar a False cuando esté estable
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name="MaestriaGeofisica",
)
