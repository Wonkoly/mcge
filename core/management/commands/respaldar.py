from django.core.management.base import BaseCommand

from core.backup import crear_respaldo


class Command(BaseCommand):
    help = "Genera un respaldo (VACUUM INTO) de la base de datos ahora mismo."

    def handle(self, *args, **options):
        destino = crear_respaldo()
        if destino is None:
            self.stdout.write(self.style.ERROR("No se pudo generar el respaldo (¿existe la base de datos?)."))
            return
        self.stdout.write(self.style.SUCCESS(f"Respaldo generado: {destino}"))
