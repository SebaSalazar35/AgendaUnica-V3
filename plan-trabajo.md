# Plan de trabajo — Eva 2 (AgendaÚnica)

Este archivo ordena **cómo vamos a pasar la ES1 a la Eva 2**.  
No reemplaza todavía a `plan.md` (eso es la Fase 5).

**Idea del profesor:** no se empieza de cero. La función `decidir()` de `solucion.py` **no se toca ni se copia**. Los datos dejan de vivir en `datos.json` y pasan a **SQLite**.

---

## Qué se queda y qué cambia (Bloque 1)

**Se queda**
- `decidir()` en `solucion.py` (4 resultados).
- `requirements.txt`, `.env` y `.env.example`.

**Cambia**
- `datos.json` deja de ser el almacenamiento.
- La vista de solo lectura (`/resumen/`) se reemplaza por **cuatro vistas CRUD**.
- Aparecen admin, login y roles.

---

## Fase 1 · Base de datos y modelo (criterio 2.1.1)

Un modelo es la ficha. Cada clave de `datos.json` se vuelve un campo.

En AgendaÚnica hoy el JSON tiene: `nombre`, `inasistencias`, `estado`.

| JSON de la ES1 | Campo del modelo | Tipo |
| --- | --- | --- |
| `nombre` | `nombre` | texto (`CharField`) |
| `inasistencias` | `inasistencias` | número (`IntegerField`) |
| `estado` | `resultado` | texto (lo que devuelve `decidir()`) |
| (nuevo) | `fecha` | fecha y hora |
| (nuevo) | `eliminado` | sí/no (borrado lógico) |
| (nuevo) | `fecha_eliminacion` | cuándo se ocultó |

Pasos del profesor:
1. Confirmar SQLite en `settings.py`.
2. Escribir el modelo en `core/models.py`.
3. `makemigrations` y `migrate`.
4. Comprobar con `makemigrations --check --dry-run` → *No changes detected*.

**Borrado lógico:** no se borra la fila; se marca `eliminado=True`.

---

## Fase 2 · Administrador de Django (criterio 2.1.2)

Registrar el modelo no basta: el admin tiene que servir para trabajar.

Pasos:
1. `list_display`, `list_filter` y `search_fields` en `admin.py`.
2. `createsuperuser`.
3. Entrar a `/admin/` y revisar: el modelo aparece, se ven columnas (no `Registro object (1)`), filtro y buscador funcionan.

---

## Fase 3 · CRUD (criterio 2.1.3)

Cuatro vistas, una por operación. `decidir()` se **importa**, no se reescribe.

| Operación | Vista | Dirección |
| --- | --- | --- |
| Leer | `lista` | `/registros/` |
| Crear | `crear` | `/registros/crear/` |
| Editar | `editar` | `/registros/<id>/editar/` |
| Eliminar (lógico) | `eliminar` | `/registros/<id>/eliminar/` |

Cuidado:
- Al editar, volver a llamar `decidir()`.
- Validar `int()` con `try/except` (si no, error 500).
- Pasar los datos viejos del JSON a la base (`cargar_datos.py`).

---

## Fase 4 · Login y roles (criterio 2.1.4)

Django ya trae usuarios. No guardar contraseñas en un modelo propio.

Tres grupos: `admin`, `normal`, `viewer`.

| Vista | Quién puede |
| --- | --- |
| Lista | cualquiera que haya entrado |
| Crear | admin y normal |
| Editar | solo admin |
| Eliminar | solo admin |

La seguridad va en un **decorador** en el servidor. Esconder un botón en el HTML **no alcanza**.

Probar escribiendo a mano `/registros/1/editar/` con el usuario de menor rango: tiene que rechazar.

Formularios POST con `{% csrf_token %}`.

---

## Fase 5 · Actualizar `ia.md` y `plan.md`

Hoy esos archivos hablan de la ES1 (sin base de datos, login en Won't). Hay que actualizarlos a SQLite, CRUD, roles y borrado lógico. Login pasa de Won't a Must.

En `ia.md`: herramienta, pregunta textual sobre modelo/migraciones/roles, y **qué corregiste** de la IA.

---

## Orden de trabajo (de a poco)

1. Fase 1 — modelo y migraciones  
2. Fase 2 — admin  
3. Fase 3 — CRUD + cargar JSON  
4. Fase 4 — login y roles  
5. Fase 5 — documentos  
6. Checklist final del PDF (`.gitignore` UTF-8, no subir `.env`, clon limpio, etc.)
