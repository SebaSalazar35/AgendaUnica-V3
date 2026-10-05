from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Perfil(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    telefono = models.CharField(max_length=20, blank=True)
    inasistencias = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class HorarioTrabajo(models.Model):
    DIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miercoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sabado"),
        (6, "Domingo"),
    ]

    dia_semana = models.IntegerField(choices=DIAS, unique=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    intervalo_minutos = models.IntegerField(default=60)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["dia_semana"]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio} - {self.hora_fin}"

    def horas(self):
        lista = []
        actual = datetime.combine(datetime.today().date(), self.hora_inicio)
        fin = datetime.combine(datetime.today().date(), self.hora_fin)
        paso = timedelta(minutes=self.intervalo_minutos)
        while actual < fin:
            lista.append(actual.time())
            actual += paso
        return lista


class Bloqueo(models.Model):
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["fecha_hora"]

    def __str__(self):
        return f"Bloqueo {self.fecha_hora}"


class Registro(models.Model):
    RESULTADO_CHOICES = [
        ("Aceptado", "Aceptado"),
        (
            "Rechazado: el cliente acumula demasiados no-show",
            "Rechazado: el cliente acumula demasiados no-show",
        ),
        (
            "Rechazado: no quedan cupos libres",
            "Rechazado: no quedan cupos libres",
        ),
        (
            "Error: cantidad de inasistencias invalida",
            "Error: cantidad de inasistencias invalida",
        ),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas",
    )
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    patente = models.CharField(max_length=10, blank=True)
    servicio = models.CharField(max_length=80, blank=True)
    inasistencias = models.IntegerField()
    resultado = models.CharField(max_length=200, choices=RESULTADO_CHOICES)
    fecha = models.DateTimeField(default=timezone.now)
    fecha_cita = models.DateTimeField(null=True, blank=True)
    # Borrado logico: no se pierde nada, solo se oculta
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    liberada = models.BooleanField(default=False)
    motivo_liberacion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["fecha_cita", "-fecha"]

    def __str__(self):
        return f"{self.nombre} {self.patente} - {self.resultado}".strip()

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()  # sin esto no guarda nada

    def liberar_por_noshow(self):
        self.liberada = True
        self.motivo_liberacion = "no-show"
        self.fecha_eliminacion = timezone.now()
        self.save()
        if self.usuario and hasattr(self.usuario, "perfil"):
            self.usuario.perfil.inasistencias += 1
            self.usuario.perfil.save()
