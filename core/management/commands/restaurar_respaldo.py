from django.core.management.base import BaseCommand, CommandError

from core.backup import listar_respaldos, restaurar_respaldo


class Command(BaseCommand):
    help = "Restaura un respaldo sobre data/maestria.db. Requiere reiniciar la app después."

    def add_arguments(self, parser):
        parser.add_argument("nombre_archivo", nargs="?", help="Nombre del archivo de respaldo a restaurar.")
        parser.add_argument("--listar", action="store_true", help="Solo lista los respaldos disponibles.")

    def handle(self, *args, **options):
        if options["listar"] or not options["nombre_archivo"]:
            for respaldo in listar_respaldos():
                self.stdout.write(respaldo.name)
            return

        try:
            restaurar_respaldo(options["nombre_archivo"])
        except FileNotFoundError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS("Respaldo restaurado. Reinicia la app para que quede todo limpio."))
