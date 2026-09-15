from django.db import models

from core.models import Lies, StatusAlumno


class Alumno(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    ciclo_ingreso = models.CharField(max_length=10, null=True, blank=True)
    status = models.ForeignKey(
        StatusAlumno, null=True, blank=True, on_delete=models.SET_NULL,
        db_column="status_codigo", related_name="alumnos",
    )
    creditos_acumulados = models.IntegerField(null=True, blank=True)
    creditos_faltantes = models.IntegerField(null=True, blank=True)
    promedio = models.FloatField(null=True, blank=True)
    ciclos_cursados = models.IntegerField(null=True, blank=True)
    maximo_ciclo = models.CharField(max_length=10, null=True, blank=True)
    # MIGE / MIGF — significado exacto sin confirmar
    dictamen = models.CharField(max_length=10, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    correo_personal = models.CharField(max_length=150, null=True, blank=True)
    correo_institucional = models.CharField(max_length=150, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    retribucion_social = models.CharField(max_length=150, null=True, blank=True)
    cvu = models.CharField(max_length=20, null=True, blank=True)
    fecha_grado = models.DateField(null=True, blank=True)
    lies = models.ForeignKey(Lies, null=True, blank=True, on_delete=models.SET_NULL, db_column="lies_id")

    tesis_titulo = models.CharField(max_length=400, null=True, blank=True)
    protocolo = models.CharField(max_length=1000, null=True, blank=True)
    impacto_cientifico = models.CharField(max_length=1000, null=True, blank=True)
    impacto_social = models.CharField(max_length=1000, null=True, blank=True)
    solucion_problemas = models.CharField(max_length=1000, null=True, blank=True)
    estrategias_acceso = models.CharField(max_length=1000, null=True, blank=True)

    observaciones = models.CharField(max_length=1000, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alumno"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
