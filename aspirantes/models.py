from django.db import models

from alumnos.models import Alumno

ESTADOS = [
    "Registrado", "Documentacion incompleta", "En evaluacion", "Entrevista",
    "Aceptado", "No aceptado", "Inscrito",
]


class Aspirante(models.Model):
    """Proceso real confirmado en actas: Evaluación Curricular 35% +
    Entrevista con profesores 30% + EXANI-III/inglés 35%, aprobación por
    Junta Académica. Al aceptarse se convierte en Alumno (alumno) sin
    recapturar datos.

    Nota de alcance: por ahora solo el modelo, para poder contar
    "aspirantes en proceso" en el Panel. La máquina de estados y el
    alta/edición completa (app/services/aspirante_service.py) se portan en
    su propia fase."""

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    licenciatura = models.CharField(max_length=150, null=True, blank=True)
    universidad = models.CharField(max_length=150, null=True, blank=True)
    promedio = models.FloatField(null=True, blank=True)
    correo = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    fecha_registro = models.DateField(null=True, blank=True)
    ciclo = models.CharField(max_length=10, null=True, blank=True)
    estado = models.CharField(max_length=30, default="Registrado")

    evaluacion_curricular = models.FloatField(null=True, blank=True)
    evaluacion_entrevista = models.FloatField(null=True, blank=True)
    evaluacion_conocimientos = models.FloatField(null=True, blank=True)

    observaciones = models.CharField(max_length=1000, null=True, blank=True)
    alumno = models.ForeignKey(Alumno, null=True, blank=True, on_delete=models.SET_NULL, db_column="alumno_id")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aspirante"

    def __str__(self):
        return self.nombre
