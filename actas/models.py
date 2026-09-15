from django.db import models

from alumnos.models import Alumno
from profesores.models import Profesor


class Acta(models.Model):
    """Acta de Junta Académica — fuente de verdad de casi todo lo demás
    (comité tutorial, dirección/codirección, lectores, sinodales).

    Nota de alcance: por ahora solo se porta el modelo (para que Dirección/
    ComiteTutorial/Lector/Sinodal puedan referenciarlo y para mostrar "según
    Acta NNN" en Alumnos/Profesores/Panel). El editor completo de actas
    (PuntoActa y la lógica de app/services/acta_service.py) se porta en su
    propia fase, no aquí."""

    id = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=30, unique=True)  # ej. "MCG/14/2022"
    fecha = models.DateField(null=True, blank=True)
    anio = models.IntegerField()
    resumen = models.CharField(max_length=500, null=True, blank=True)

    hora_inicio = models.CharField(max_length=10, null=True, blank=True)
    hora_fin = models.CharField(max_length=10, null=True, blank=True)
    lugar = models.CharField(max_length=150, null=True, blank=True, default="Puerto Vallarta, Jalisco")
    sede = models.CharField(max_length=250, null=True, blank=True)
    asistentes = models.CharField(max_length=1000, null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "acta"
        ordering = ["-numero"]

    def __str__(self):
        return self.numero


class Direccion(models.Model):
    """Relación alumno<->profesor como Director o Codirector de tesis. Con
    historial real: al cambiar de director, la fila anterior se cierra con
    `fecha_fin` (no se borra) y se crea una nueva."""

    ROLES = (("Director", "Director"), ("Codirector", "Codirector"))

    id = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="alumno_id", related_name="direcciones")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, db_column="profesor_id", related_name="direcciones")
    rol = models.CharField(max_length=12, choices=ROLES)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)  # NULL = vigente
    acta = models.ForeignKey(Acta, null=True, blank=True, on_delete=models.SET_NULL, db_column="acta_id")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "direccion"

    def __str__(self):
        return f"{self.profesor} - {self.rol} de {self.alumno}"

    @property
    def vigente(self) -> bool:
        return self.fecha_fin is None


class ComiteTutorial(models.Model):
    """Comité tutorial de un alumno para un ciclo: 2-3 profesores, sin cargo
    diferenciado (lista plana vía ComiteMiembro), reasignable por ciclo —
    por eso lleva fecha_inicio/fecha_fin igual que Dirección."""

    id = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="alumno_id", related_name="comites_tutoriales")
    ciclo = models.CharField(max_length=10, null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)  # NULL = vigente
    acta = models.ForeignKey(Acta, null=True, blank=True, on_delete=models.SET_NULL, db_column="acta_id")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comite_tutorial"

    def __str__(self):
        return f"Comité de {self.alumno} ({self.ciclo or 'sin ciclo'})"

    @property
    def vigente(self) -> bool:
        return self.fecha_fin is None


class ComiteMiembro(models.Model):
    """Un profesor dentro de un ComiteTutorial. Sin columna `cargo`: los
    datos reales de las actas no distinguen roles dentro del comité
    tutorial (a diferencia de Sinodal)."""

    id = models.AutoField(primary_key=True)
    comite = models.ForeignKey(ComiteTutorial, on_delete=models.CASCADE, db_column="comite_id", related_name="miembros")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, db_column="profesor_id")

    class Meta:
        db_table = "comite_miembro"

    def __str__(self):
        return str(self.profesor)


class Lector(models.Model):
    """3 personas por tesis, propuestas por el director y aprobadas en
    Acta, certifican que el documento de tesis está terminado."""

    id = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="alumno_id", related_name="lectores")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, db_column="profesor_id")
    fecha = models.DateField(null=True, blank=True)
    acta = models.ForeignKey(Acta, null=True, blank=True, on_delete=models.SET_NULL, db_column="acta_id")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lector"

    def __str__(self):
        return f"{self.profesor} lector de {self.alumno}"


class Sinodal(models.Model):
    """Jurado de examen de grado: Presidente/Secretario/Vocal — sí tiene
    cargo diferenciado (a diferencia del comité tutorial)."""

    CARGOS = (("Presidente", "Presidente"), ("Secretario", "Secretario"), ("Vocal", "Vocal"))

    id = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="alumno_id", related_name="sinodales")
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, db_column="profesor_id")
    cargo = models.CharField(max_length=15, null=True, blank=True, choices=CARGOS)
    fecha_examen = models.DateField(null=True, blank=True)
    hora_examen = models.CharField(max_length=10, null=True, blank=True)
    lugar_examen = models.CharField(max_length=200, null=True, blank=True)
    acta = models.ForeignKey(Acta, null=True, blank=True, on_delete=models.SET_NULL, db_column="acta_id")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sinodal"

    def __str__(self):
        return f"{self.profesor} ({self.cargo}) - {self.alumno}"
