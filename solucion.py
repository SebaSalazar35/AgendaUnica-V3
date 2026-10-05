# AgendaUnica
# Fase 3: la vista de Django importa decidir() desde este archivo.

import json
import os

from tabulate import tabulate

# datos.json queda junto a este archivo y junto a manage.py
archivo = os.path.join(os.path.dirname(__file__), "datos.json")
CUPOS = 3


def decidir(inasistencias, cupos):
    # El dato invalido va primero. Si lo dejo al final, nunca se revisa.
    if inasistencias < 0:
        return "Error: cantidad de inasistencias invalida"
    elif inasistencias < 2 and cupos > 0:
        return "Aceptado"
    elif inasistencias >= 2:
        return "Rechazado: el cliente acumula demasiados no-show"
    else:
        return "Rechazado: no quedan cupos libres"


def cupos_libres(registros):
    # Solo los aceptados ocupan un cupo. Un rechazo no consume nada.
    ocupados = 0
    for r in registros:
        if r["estado"] == "Aceptado":
            ocupados = ocupados + 1
    return CUPOS - ocupados


def cargar():
    if os.path.exists(archivo):
        with open(archivo, encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar(registros):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=2)


if __name__ == "__main__":
    nombre = input("Nombre del cliente: ")
    inasistencias = int(input("Inasistencias (no-show) previas: "))

    registros = cargar()
    estado = decidir(inasistencias, cupos_libres(registros))
    print(estado)

    # Guardar: json ya viene con Python, no se instala
    registros.append(
        {"nombre": nombre, "inasistencias": inasistencias, "estado": estado}
    )
    guardar(registros)

    # Mostrar: tabulate SI se instala con pip
    print()
    print(tabulate(registros, headers="keys"))
