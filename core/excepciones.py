from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken


def manejar_errores(exc, context):
    """Deja todos los errores de la API en espanol y con la forma {"detail": ...}."""
    if isinstance(exc, Http404):
        return Response(
            {"detail": "No existe un registro con ese id."},
            status=status.HTTP_404_NOT_FOUND,
        )

    respuesta = exception_handler(exc, context)
    if respuesta is None:
        return None

    if isinstance(exc, InvalidToken):
        respuesta.data = {
            "detail": "El token no es valido o ya vencio. Pide uno nuevo en /api/token/ o /api/token/refresh/.",
        }
    elif isinstance(exc, AuthenticationFailed) and exc.get_codes() == "no_active_account":
        respuesta.data = {"detail": "Usuario o contrasena incorrectos."}
    return respuesta
