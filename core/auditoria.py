from core.models import HistorialCambio


def registrar(
    *,
    usuario: str,
    entidad: str,
    entidad_id: int,
    accion: str,
    campo: str | None = None,
    valor_anterior: str | None = None,
    valor_nuevo: str | None = None,
) -> None:
    HistorialCambio.objects.create(
        usuario=usuario,
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        campo=campo,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
    )
