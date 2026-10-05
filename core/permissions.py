from rest_framework import permissions

from core.roles import tiene_rol


class PermisoPorRol(permissions.BasePermission):
    """
    Mismos roles que las pantallas de la ES2:
    - cualquier usuario autenticado lee (GET)
    - admin y normal crean (POST)
    - solo admin edita (PUT/PATCH) y borra (DELETE)
    """

    message = "Tu rol no tiene permiso para esta operacion."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return tiene_rol(request.user, "admin", "normal")
        return tiene_rol(request.user, "admin")
