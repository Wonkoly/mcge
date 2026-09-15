"""Puentes Flask -> Django expuestos como variables de contexto (no globals,
porque necesitan el `request` de la petición en curso)."""

from django.contrib import messages
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe

_CATEGORIA_POR_NIVEL = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "exito",
    messages.WARNING: "aviso",
    messages.ERROR: "error",
}


def jinja_helpers(request):
    def get_flashed_messages(with_categories=False):
        mensajes = messages.get_messages(request)
        if with_categories:
            return [(_CATEGORIA_POR_NIVEL.get(m.level, "info"), str(m)) for m in mensajes]
        return [str(m) for m in mensajes]

    def csrf_input():
        token = get_token(request)
        return mark_safe(f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">')

    return {
        "get_flashed_messages": get_flashed_messages,
        "csrf_input": csrf_input,
    }
