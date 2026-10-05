# AgendaUnica V3 · API REST

Taller mecanico. ES3 de Programacion Back End (INACAP). Sebastian Salazar.

La ES2 sigue entera: modelos, migraciones, admin y pantallas HTML. Encima se agrega una API REST con Django REST Framework bajo `/api/`, sobre los mismos modelos y la misma base. La regla de la ES1 (`decidir()` en `solucion.py`) es la que decide el `resultado` tambien en la API.

## Como levantarlo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # y llenar SECRET_KEY y las PASS_*
python manage.py migrate
python manage.py crear_usuarios
python manage.py cargar_datos
python manage.py runserver
```

- Pantallas HTML (ES2): http://127.0.0.1:8000/login/
- Documentacion de la API (Swagger): http://127.0.0.1:8000/api/docs/
- Tests automaticos de la API: `python manage.py test core`

## Usuarios y roles

Las contrasenas de prueba van en el `.env` (`PASS_ADMIN`, `PASS_NORMAL`, `PASS_VIEWER`, `PASS_CLIENTE`). El `.env` no se sube.

| Usuario | Pantallas HTML (ES2) | API (ES3) |
| --- | --- | --- |
| admin | todo, agenda y `/admin/` | leer, crear, editar y borrar |
| normal | crear registros | leer y crear |
| viewer | solo mirar la lista | solo leer |
| cliente | pedir hora en el calendario | solo leer |

## Endpoints de la API

Todas las rutas, salvo las del token y la documentacion, piden `Authorization: Bearer <access>`.

| Metodo | Ruta | Que hace | Quien | Respuesta OK |
| --- | --- | --- | --- | --- |
| POST | `/api/token/` | Entrega `access` (30 min) y `refresh` (1 dia) con usuario y clave | publico | 200 |
| POST | `/api/token/refresh/` | Entrega un `access` nuevo a partir del `refresh` | publico | 200 |
| GET | `/api/registros/` | Lista registros, paginado de a 10 (`?page=2`) y con filtros | autenticado | 200 |
| POST | `/api/registros/` | Crea un registro; `resultado` lo calcula `decidir()` | admin, normal | 201 |
| GET | `/api/registros/{id}/` | Muestra uno | autenticado | 200 |
| PUT | `/api/registros/{id}/` | Reemplaza el registro completo y recalcula `resultado` | admin | 200 |
| PATCH | `/api/registros/{id}/` | Cambia solo los campos enviados y recalcula `resultado` | admin | 200 |
| DELETE | `/api/registros/{id}/` | Borrado logico (`eliminado=True`), igual que la ES2 | admin | 204 |
| GET | `/api/registros/aceptados/` | Solo los aceptados vigentes, paginado | autenticado | 200 |
| GET | `/api/docs/` | Swagger para leer y probar la API | publico | 200 |
| GET | `/api/schema/` | Esquema OpenAPI | publico | 200 |

Filtros de la lista (se pueden combinar con `?page=`):

| Parametro | Ejemplo | Que filtra |
| --- | --- | --- |
| `resultado` | `?resultado=Aceptado` | resultado exacto |
| `patente` | `?patente=bcdf-23` | patente exacta (se normaliza a `BCDF23`) |
| `nombre` | `?nombre=maria` | parte del nombre, sin importar mayusculas |

Errores que devuelve, siempre como `{"detail": "..."}` en espanol (`core/excepciones.py`), salvo el 400 que dice que campo fallo y por que:

| Codigo | Cuando | Mensaje |
| --- | --- | --- |
| 400 | el JSON no pasa la validacion | `{"inasistencias": ["Las inasistencias no pueden ser negativas."]}` |
| 401 | sin token | `Las credenciales de autenticación no se proveyeron.` |
| 401 | clave mala en `/api/token/` | `Usuario o contrasena incorrectos.` |
| 401 | token falso o vencido | `El token no es valido o ya vencio. ...` |
| 403 | tu rol no puede hacer esa operacion | `Tu rol no tiene permiso para esta operacion.` |
| 404 | el id no existe o fue borrado | `No existe un registro con ese id.` |

Campos del registro: `id`, `nombre`, `telefono`, `patente`, `servicio`, `inasistencias`, `resultado` (solo lectura), `fecha` (solo lectura), `fecha_cita`.

## Ejemplo con curl

```bash
# 1. pedir el token con un usuario de la ES2
curl -X POST -H "Content-Type: application/json" \
  -d '{"username": "normal", "password": "TU_CLAVE"}' \
  http://127.0.0.1:8000/api/token/
# {"refresh":"eyJhbGciOiJI...","access":"eyJhbGciOiJI..."}

# 2. mandarlo en la cabecera de cada peticion
curl -H "Authorization: Bearer eyJhbGciOiJI..." http://127.0.0.1:8000/api/registros/

# 3. crear
curl -X POST -H "Authorization: Bearer eyJhbGciOiJI..." -H "Content-Type: application/json" \
  -d '{"nombre": "Pedro Rojas", "patente": "BCDF23", "inasistencias": 0}' \
  http://127.0.0.1:8000/api/registros/
```

La evidencia completa de las 20 pruebas (casos buenos y malos) esta en `pruebas/salida_curl.txt`. Se regenera con el servidor corriendo:

```powershell
powershell -ExecutionPolicy Bypass -File pruebas\probar_api.ps1
```

## Por que esta configuracion

- **JWT y no sesion:** quien consume una API es otro programa, sin navegador ni cookie. El token va en la cabecera de cada peticion. Elegi JWT (simplejwt) y no el token simple de DRF porque el JWT caduca: si se filtra un `access`, sirve 30 minutos y no para siempre. El `refresh` dura un dia y permite pedir otro `access` sin volver a mandar la clave.
- **`IsAuthenticated` por defecto:** si mañana agrego un endpoint y me olvido de ponerle permiso, nace cerrado y no abierto. Encima de eso, `PermisoPorRol` (`core/permissions.py`) repite los mismos roles de la ES2: viewer lee, normal crea y solo admin edita y borra.
- **`PAGE_SIZE` 10:** la agenda crece todos los dias. Devolver todo en una sola respuesta se vuelve lento; 10 es lo que cabe en una pantalla y el cliente pide la siguiente con `?page=`.
- **Un solo estilo de vista (`ModelViewSet`):** el recurso es un CRUD completo, asi que el ViewSet con router da las cinco operaciones con rutas REST sin escribirlas a mano. No mezclo `APIView` ni `generics`.
- **`resultado` de solo lectura:** lo decide `decidir()` en `perform_create`/`perform_update`. Si el cliente pudiera mandarlo, cualquiera se declararia "Aceptado".
- **Filtros por parametro y no rutas nuevas:** filtrar una coleccion no es otro recurso, asi que va como `?resultado=` sobre `/api/registros/` en vez de inventar rutas como `/api/registros-rechazados/`. Los hice a mano en `get_queryset` para no sumar otra dependencia (`django-filter`) por tres filtros simples.
- **Errores en un solo idioma y formato:** DRF y simplejwt mezclaban espanol e ingles, y el 401 del token traia una lista interna. `core/excepciones.py` deja todo como `{"detail": "..."}` en espanol, para que quien consuma la API lea siempre la misma forma.
- **Borrado logico en la API:** el DELETE responde 204 pero marca `eliminado=True`, igual que la pantalla de eliminar de la ES2. Las dos interfaces se comportan igual sobre el mismo dato.

## Archivos nuevos de la ES3

| Archivo | Que tiene |
| --- | --- |
| `core/serializers.py` | `RegistroSerializer`: campos enumerados, `resultado` read-only, validaciones |
| `core/api_views.py` | `RegistroViewSet` con la regla de negocio, filtros y la accion `aceptados` |
| `core/permissions.py` | `PermisoPorRol`: permisos diferenciados por grupo |
| `core/excepciones.py` | manejador de errores: mensajes claros y en espanol |
| `core/tests.py` | 15 tests de la API (200, 201, 204, 400, 401, 403, 404, filtros, refresh) |
| `miproyecto/settings.py` | `INSTALLED_APPS`, `REST_FRAMEWORK`, `SIMPLE_JWT` |
| `miproyecto/urls.py` | router en `/api/`, token, refresh y Swagger |
| `pruebas/` | script de curl y su salida |
| `ia.md` | uso critico de IA |
