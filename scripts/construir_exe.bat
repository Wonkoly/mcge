@echo off
REM Construye el .exe (modo --onedir) en Windows. Debe correr en Windows —
REM PyInstaller no genera un .exe de Windows desde Linux/Mac.
REM
REM Uso: doble clic, o desde cmd: scripts\construir_exe.bat

cd /d "%~dp0\.."

if not exist .venv (
    echo Creando entorno virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Instalando dependencias (incluye PyInstaller)...
pip install -r requirements-build.txt

echo Construyendo MaestriaGeofisica (modo onedir)...
pyinstaller mcg.spec --noconfirm

echo.
echo Listo. La app quedo en: dist\MaestriaGeofisica\
echo Copia esa carpeta COMPLETA a donde se vaya a usar — no solo el .exe.
pause
