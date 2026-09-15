from django.db import models


class StatusAlumno(models.Model):
    """Catálogo de códigos de status de alumno, tomados de la hoja `Estatus`
    del Excel. `confirmado=False` marca códigos cuyo significado exacto
    (B8, RD) sigue pendiente de confirmar con el usuario."""

    codigo = models.CharField(max_length=4, primary_key=True)
    nombre = models.CharField(max_length=60)
    # activo|baja|proceso_titulacion|graduado|titulado|inactivo
    categoria = models.CharField(max_length=20)
    confirmado = models.BooleanField(default=True)

    class Meta:
        db_table = "status_alumno"

    def __str__(self):
        return self.nombre


class Lies(models.Model):
    """Líneas de Investigación e Incidencia Social — catálogo oficial de 2
    valores (cuc.udg.mx), compartido por Alumno y Profesor."""

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "lies"

    def __str__(self):
        return self.nombre


class Configuracion(models.Model):
    """Ajustes de la app en un solo lugar (no repartidos en el código):
    ruta de respaldos, ciclo escolar actual, coordinador por defecto, etc.
    Clave/valor simple — ver core/configuracion.py para las claves
    conocidas y sus valores por defecto."""

    clave = models.CharField(max_length=60, primary_key=True)
    valor = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "configuracion"

    def __str__(self):
        return self.clave


class HistorialCambio(models.Model):
    ACCIONES = (("crear", "crear"), ("modificar", "modificar"), ("eliminar", "eliminar"))

    id = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=80, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    entidad = models.CharField(max_length=50)
    entidad_id = models.IntegerField()
    accion = models.CharField(max_length=20, choices=ACCIONES)
    campo = models.CharField(max_length=50, null=True, blank=True)
    valor_anterior = models.CharField(max_length=500, null=True, blank=True)
    valor_nuevo = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "historial_cambio"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.entidad}#{self.entidad_id} {self.accion}"
