from core.roles import es_admin, tiene_rol


def roles(request):
    # Esto lo usan las plantillas para mostrar o esconder botones.
    # La seguridad de verdad esta en el decorador, no aca.
    user = request.user
    return {
        "es_admin": es_admin(user),
        "es_normal": tiene_rol(user, "normal"),
        "es_viewer": tiene_rol(user, "viewer"),
        "es_cliente": tiene_rol(user, "cliente"),
        "puede_crear": tiene_rol(user, "admin", "normal"),
        "puede_editar": es_admin(user),
    }
