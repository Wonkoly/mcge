from django.db import models


class FolioSecuencia(models.Model):
    """Contador de folios por tipo de documento y año, con incremento
    atómico (ver documentos/folios.py) para que dos PCs pidiendo folio casi
    al mismo tiempo nunca reciban el mismo número. La secuencia reinicia
    sola cada año porque la clave incluye `anio`. El incremento real se
    hace con SQL crudo (INSERT ... ON CONFLICT ... RETURNING) — este modelo
    existe para que la tabla quede declarada (migraciones, `manage.py test`
    con base de pruebas), no para escribirle vía el ORM."""

    tipo_documento = models.CharField(max_length=60)
    anio = models.IntegerField()
    ultimo_folio = models.IntegerField(default=0)
    pk = models.CompositePrimaryKey("tipo_documento", "anio")

    class Meta:
        db_table = "folio_secuencia"

    def __str__(self):
        return f"{self.tipo_documento} {self.anio}: {self.ultimo_folio}"
