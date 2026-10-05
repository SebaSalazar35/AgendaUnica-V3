# Plan — Taller mecanico (Eva 2)

## Apartado de negocio

**Problema.** En un taller la agenda se anota en WhatsApp y en un cuaderno. Se cruzan dos vehiculos en la misma hora y clientes que no se presentan (no-show) vuelven a reservar. Cada hora perdida deja de cobrarse.

**Solucion.** Un programa que guarda cada ficha en SQLite, decide con la regla ya hecha si se acepta la hora, y deja entrar solo a quien corresponde: unos anotan, otros solo miran.

**Alcance.** Entra: modelo y migraciones, administrador de Django, CRUD, login con roles, borrado logico, calendario del taller y confirmacion por WhatsApp. No entra: pagos ni una API.

**MoSCoW.**

| Prioridad | Funcion |
| --- | --- |
| Must | Guardar en SQLite con un modelo |
| Must | Decidir con los 4 resultados (se importa, no se copia) |
| Must | CRUD: crear, listar, editar y eliminar logico |
| Must | Cuentas de usuario con contrasena y tres roles |
| Should | Calendario de horas y bloqueo automatico |
| Could | Confirmar la hora por WhatsApp |
| Won't | Cobros ni integracion real con el WhatsApp Business API |

**MVP** = los cuatro Must. El calendario y WhatsApp son extra, no reemplazan el CRUD.

---

## Apartado tecnico

**Datos de entrada.** `nombre` (texto) e `inasistencias` (entero, con `int()` y `try/except`). En el taller tambien se pide patente y servicio. `cupos` se calcula como 3 menos las reservas aceptadas vigentes. Un rechazo no ocupa cupo.

**Regla de decision.** Sigue en `solucion.py`. Las vistas hacen `from solucion import decidir`. Al editar se vuelve a llamar. Los 4 resultados, en este orden:

| # | Condicion | Resultado |
| --- | --- | --- |
| 1 | inasistencias < 0 | Error: cantidad de inasistencias invalida |
| 2 | inasistencias < 2 **y** cupos > 0 | Aceptado |
| 3 | inasistencias >= 2 | Rechazado: el cliente acumula demasiados no-show |
| 4 | resto (cupos == 0) | Rechazado: no quedan cupos libres |

**Base de datos.** SQLite (`db.sqlite3`). El modelo `Registro` tiene los campos del JSON mas `fecha`, `eliminado` y `fecha_eliminacion`. El borrado es logico: `soft_delete()`.

**CRUD.** `/registros/`, `/registros/crear/`, `/registros/<id>/editar/`, `/registros/<id>/eliminar/`.

**Roles.** Grupos de Django: `admin`, `normal`, `viewer`. La lista la ve quien entro. Crear: admin y normal. Editar y eliminar: solo admin. La traba va en un decorador, no solo en el HTML. El grupo `cliente` es extra para el calendario del taller.

**Paquete externo.** `tabulate` (consola) y `python-decouple` (claves en `.env`).
