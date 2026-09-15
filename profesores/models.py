from django.db import models

from core.models import Lies

TRATAMIENTOS = ["Doctor", "Doctora", "Maestro", "Maestra"]

PREFIJO_POR_TRATAMIENTO = {
    "Doctor": "Dr.",
    "Doctora": "Dra.",
    "Maestro": "Mtro.",
    "Maestra": "Mtra.",
}

CENTRO_UNIVERSITARIO_DEFAULT = "Centro Universitario de la Costa"


class Profesor(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, unique=True)
    # catálogo cerrado: TRATAMIENTOS — para el prefijo en documentos
    tratamiento = models.CharField(max_length=10, null=True, blank=True)
    # disciplina/grado en texto libre, informativo — NO entra a los documentos
    grado = models.CharField(max_length=150, null=True, blank=True)
    centro_universitario = models.CharField(max_length=150, null=True, blank=True, default=CENTRO_UNIVERSITARIO_DEFAULT)
    cvu = models.CharField(max_length=20, null=True, blank=True)
    correo = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    nucleo_academico = models.BooleanField(default=False)
    sni = models.CharField(max_length=10, null=True, blank=True)
    dedicacion = models.CharField(max_length=60, null=True, blank=True)
    linea_investigacion = models.CharField(max_length=200, null=True, blank=True)
    lies = models.ForeignKey(Lies, null=True, blank=True, on_delete=models.SET_NULL, db_column="lies_id")
    activo = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=500, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profesor"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def prefijo(self) -> str:
        return PREFIJO_POR_TRATAMIENTO.get(self.tratamiento or "", "")


class ProfesorAlias(models.Model):
    """Variantes de nombre encontradas en el Excel/actas para un mismo
    profesor (typos, acentos, prefijos Dr./Dra./Mtro.) — permite reconciliar
    texto libre histórico sin perder la referencia a qué persona real es."""

    id = models.AutoField(primary_key=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, db_column="profesor_id", related_name="alias")
    alias = models.CharField(max_length=150)

    class Meta:
        db_table = "profesor_alias"

    def __str__(self):
        return self.alias
