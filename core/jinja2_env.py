"""Entorno Jinja2 para Django, pensado para que las plantillas heredadas de
Flask (macros/ui.html y todo lo que las usa) sigan funcionando casi sin
tocarlas. Ver la sección "Decisión de arquitectura clave" del plan de
migración.
"""

import itertools
from urllib.parse import urlencode

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import NoReverseMatch, reverse
from jinja2 import Environment


def _url_for(endpoint, **values):
    """Compatible con el `url_for` de Flask:

    - `url_for('static', filename=...)` sigue funcionando tal cual.
    - Los endpoints con punto ("profesores.listar", estilo blueprint de
      Flask) se traducen a la notación con dos puntos de Django
      ("profesores:listar"), así las plantillas portadas no se tocan.
    - Cualquier kwarg que no forme parte de la ruta se agrega como query
      string, igual que hacía Flask (p. ej. filtros del panel:
      `url_for('alumnos.listar', status='AC')`).
    """
    if endpoint == "static":
        return staticfiles_storage.url(values.get("filename", ""))

    values.pop("_external", None)
    if "." in endpoint and ":" not in endpoint:
        endpoint = endpoint.replace(".", ":", 1)

    try:
        return reverse(endpoint, kwargs=values)
    except NoReverseMatch:
        if not values:
            raise

    for n in range(len(values) - 1, -1, -1):
        for combo in itertools.combinations(values.items(), n):
            path_kwargs = dict(combo)
            try:
                url = reverse(endpoint, kwargs=path_kwargs)
            except NoReverseMatch:
                continue
            extra = {k: v for k, v in values.items() if k not in path_kwargs}
            return f"{url}?{urlencode(extra)}" if extra else url
    raise NoReverseMatch(endpoint)


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "url_for": _url_for,
            "static": lambda path: staticfiles_storage.url(path),
        }
    )
    return env
