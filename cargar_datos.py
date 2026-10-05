# Pasa los datos viejos de datos.json a SQLite.
# Se corre con:
# python manage.py shell < cargar_datos.py

import json

from core.models import Registro

for r in json.load(open("datos.json", encoding="utf-8")):
    Registro.objects.create(
        nombre=r["nombre"],
        inasistencias=r["inasistencias"],
        resultado=r["estado"],
    )
