from django.contrib import admin

from core.models import Bloqueo, HorarioTrabajo, Perfil, Registro


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "patente",
        "servicio",
        "fecha_cita",
        "inasistencias",
        "resultado",
        "liberada",
        "fecha",
    )
    list_filter = ("resultado", "eliminado", "liberada")
    search_fields = ("nombre", "patente")
    readonly_fields = ("fecha_eliminacion",)


@admin.register(HorarioTrabajo)
class HorarioTrabajoAdmin(admin.ModelAdmin):
    list_display = ("dia_semana", "hora_inicio", "hora_fin", "intervalo_minutos", "activo")
    list_filter = ("activo",)


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "motivo")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "telefono", "inasistencias")
    search_fields = ("user__username",)
