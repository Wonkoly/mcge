"""Shim de compatibilidad: expone `request.endpoint`/`request.blueprint`
como los tenía Flask, para que las plantillas portadas (p. ej. resaltar el
enlace de navegación activo) no se tengan que reescribir."""


class FlaskCompatMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if match is None:
            return None
        request.blueprint = match.app_name or None
        request.endpoint = f"{match.app_name}.{match.url_name}" if match.app_name else match.url_name
        return None

    def __call__(self, request):
        return self.get_response(request)
