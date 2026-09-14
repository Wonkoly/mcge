"""Resolución de rutas que funciona igual en desarrollo y empaquetado con
PyInstaller (--onedir). PyInstaller NO preserva la estructura de carpetas
del código fuente: los .py quedan embebidos, y los `datas` (plantillas,
estáticos, logo) se extraen junto al ejecutable, accesibles vía
`sys._MEIPASS`. Sin esto, cualquier ruta calculada con
`Path(__file__).resolve().parent...` se rompe en el .exe aunque funcione
perfecto en `python main.py`.

Dos categorías de ruta, porque no es lo mismo:
- Recursos de solo lectura que van EMPAQUETADOS (plantillas Jinja, CSS/JS,
  plantillas .docx, el logo) -> `directorio_recursos()`.
- Datos que la app ESCRIBE (la base de datos, los respaldos) -> deben vivir
  junto al .exe, nunca dentro del paquete -> `directorio_datos()`.
"""

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent


def congelado() -> bool:
    return getattr(sys, "frozen", False)


def directorio_recursos() -> Path:
    if congelado():
        return Path(sys._MEIPASS)  # carpeta temporal/onedir donde PyInstaller puso los `datas`
    return RAIZ_PROYECTO


def directorio_datos() -> Path:
    if congelado():
        return Path(sys.executable).resolve().parent  # junto al .exe, no dentro del paquete
    return RAIZ_PROYECTO


def directorio_plantillas_personalizadas() -> Path:
    """Moldes base y plantillas de tipos de documento personalizados
    subidos desde la app (Documentos → taller de plantillas) — escribible,
    junto a data/ y backups/, para sobrevivir actualizaciones del .exe."""
    ruta = directorio_datos() / "plantillas_personalizadas"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
