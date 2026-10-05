from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Registro
from core.patente import normalizar_patente
from core.permissions import PermisoPorRol
from core.serializers import RegistroSerializer
from core.views import cupos_para
from solucion import decidir

FILTROS = [
    OpenApiParameter(
        "resultado",
        str,
        description='Resultado exacto, por ejemplo "Aceptado".',
    ),
    OpenApiParameter("patente", str, description="Patente exacta, ABCD12 o AB1234."),
    OpenApiParameter("nombre", str, description="Parte del nombre del cliente."),
]


@extend_schema_view(
    list=extend_schema(parameters=FILTROS),
    aceptados=extend_schema(parameters=FILTROS[1:]),
)
class RegistroViewSet(viewsets.ModelViewSet):
    queryset = Registro.objects.filter(eliminado=False).order_by("-fecha")
    serializer_class = RegistroSerializer
    permission_classes = [PermisoPorRol]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action not in ("list", "aceptados"):
            return qs
        params = self.request.query_params
        if params.get("resultado"):
            qs = qs.filter(resultado=params["resultado"])
        if params.get("patente"):
            qs = qs.filter(patente=normalizar_patente(params["patente"]))
        if params.get("nombre"):
            qs = qs.filter(nombre__icontains=params["nombre"].strip())
        return qs

    def perform_create(self, serializer):
        inasistencias = serializer.validated_data["inasistencias"]
        serializer.save(resultado=decidir(inasistencias, cupos_para()))

    def perform_update(self, serializer):
        # En un PATCH puede no venir inasistencias: uso el valor guardado.
        registro = serializer.instance
        inasistencias = serializer.validated_data.get(
            "inasistencias", registro.inasistencias
        )
        serializer.save(
            resultado=decidir(inasistencias, cupos_para(excepto=registro.pk))
        )

    def perform_destroy(self, instance):
        # Mismo borrado logico que la ES2: el dato no se pierde.
        instance.soft_delete()

    @action(detail=False, methods=["get"])
    def aceptados(self, request):
        qs = self.get_queryset().filter(resultado="Aceptado", liberada=False)
        pagina = self.paginate_queryset(qs)
        if pagina is not None:
            return self.get_paginated_response(
                self.get_serializer(pagina, many=True).data
            )
        return Response(
            self.get_serializer(qs, many=True).data, status=status.HTTP_200_OK
        )
