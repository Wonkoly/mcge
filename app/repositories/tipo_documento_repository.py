from sqlalchemy.orm import Session

from app.models import PlantillaBase, TipoDocumentoPersonalizado


def listar_tipos(session: Session) -> list[TipoDocumentoPersonalizado]:
    return session.query(TipoDocumentoPersonalizado).order_by(TipoDocumentoPersonalizado.etiqueta).all()


def listar_tipos_confirmados(session: Session) -> list[TipoDocumentoPersonalizado]:
    return (
        session.query(TipoDocumentoPersonalizado)
        .filter(TipoDocumentoPersonalizado.estado == "confirmado")
        .order_by(TipoDocumentoPersonalizado.etiqueta)
        .all()
    )


def obtener_tipo(session: Session, tipo_id: int) -> TipoDocumentoPersonalizado | None:
    return session.get(TipoDocumentoPersonalizado, tipo_id)


def obtener_molde(session: Session, categoria: str) -> PlantillaBase | None:
    return session.get(PlantillaBase, categoria)


def listar_moldes(session: Session) -> dict[str, PlantillaBase]:
    return {m.categoria: m for m in session.query(PlantillaBase).all()}
