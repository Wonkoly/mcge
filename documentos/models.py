from django.db import models


class PlantillaBase(models.Model):
    """Molde en blanco (solo membrete — header/footer con logos, cuerpo
    vacío) subido una vez por categoría. Sobre este molde se componen los
    tipos de documento personalizados — el cuerpo se agrega como texto
    plano en la app, nunca se toca el header/footer, así el acomodo de
    imágenes nunca se desarma."""

    categoria = models.CharField(max_length=20, primary_key=True)  # "oficio" | "constancia"
    archivo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "plantilla_base"

    def __str__(self):
        return f"{self.categoria}: {self.archivo or 'sin subir'}"


class TipoDocumentoPersonalizado(models.Model):
    """Un tipo de oficio/constancia definido por el coordinador desde el
    taller de plantillas, sin tocar código. `cuerpo_texto` es lo que se
    redactó en el editor (texto plano, un renglón = un párrafo, con
    {{ variables }} literales insertadas desde el panel de datos
    disponibles). `plantilla_archivo` es el .docx ya compilado (molde de
    PlantillaBase + cuerpo_texto), listo para docxtpl. Solo los
    "confirmado" aparecen como opción al agregar un punto de Acta."""

    ESTADOS = (("borrador", "Borrador"), ("confirmado", "Confirmado"))

    id = models.AutoField(primary_key=True)
    clave = models.CharField(max_length=60, unique=True)
    etiqueta = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, null=True, blank=True)
    categoria = models.CharField(max_length=20)
    cuerpo_texto = models.TextField(null=True, blank=True)
    plantilla_archivo = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tipo_documento_personalizado"
        ordering = ["etiqueta"]

    def __str__(self):
        return self.etiqueta


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
