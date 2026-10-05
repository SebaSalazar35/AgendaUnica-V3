from rest_framework import serializers

from core.models import Registro
from core.patente import normalizar_patente, patente_valida


class RegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registro
        # Campos enumerados a mano: eliminado, usuario y liberada no salen.
        fields = [
            "id",
            "nombre",
            "telefono",
            "patente",
            "servicio",
            "inasistencias",
            "resultado",
            "fecha",
            "fecha_cita",
        ]
        # resultado lo decide decidir(), nunca el cliente.
        read_only_fields = ["resultado", "fecha"]

    def validate_nombre(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("El nombre no puede ir vacio.")
        return valor

    def validate_inasistencias(self, valor):
        if valor < 0:
            raise serializers.ValidationError(
                "Las inasistencias no pueden ser negativas."
            )
        return valor

    def validate_patente(self, valor):
        patente = normalizar_patente(valor)
        if patente and not patente_valida(patente):
            raise serializers.ValidationError(
                "La patente no es valida. Usa ABCD12 o AB1234."
            )
        return patente
