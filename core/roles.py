from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def tiene_rol(user, *roles):
    # Si no ha entrado, no tiene ningun rol
    if not user.is_authenticated:
        return False
    # El superusuario puede todo
    if user.is_superuser:
        return True
    for rol in roles:
        if user.groups.filter(name=rol).exists():
            return True
    return False


def es_admin(user):
    return tiene_rol(user, "admin")


def a_donde_va(user):
    # Cada tipo de usuario cae en una pantalla distinta
    if es_admin(user):
        return "panel"
    if tiene_rol(user, "cliente"):
        return "calendario"
    return "lista"


def requiere_rol(*roles):
    # Esto se pone arriba de la vista. Si no tiene el rol, no entra.
    def decorador(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):
            if tiene_rol(request.user, *roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No puedes entrar a esta parte.")
            return redirect(a_donde_va(request.user))

        return wrapper

    return decorador
