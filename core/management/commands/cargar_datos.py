import json
from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import Registro


class Command(BaseCommand):
    help = "Pasa datos.json a la tabla Registro."

    def handle(self, *args, **options):
        ruta = Path(__file__).resolve().parents[3] / "datos.json"
        creados = 0
        for r in json.loads(ruta.read_text(encoding="utf-8")):
            _, nuevo = Registro.objects.get_or_create(
                nombre=r["nombre"],
                inasistencias=r["inasistencias"],
                resultado=r["estado"],
                defaults={"eliminado": False},
            )
            if nuevo:
                creados += 1
        self.stdout.write(self.style.SUCCESS(f"Cargados {creados} registros nuevos."))
