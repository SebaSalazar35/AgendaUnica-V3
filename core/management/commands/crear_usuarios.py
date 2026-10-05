from datetime import time

from decouple import config
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from core.models import HorarioTrabajo, Perfil


class Command(BaseCommand):
    help = "Crea grupos, usuarios de prueba y horarios de trabajo."

    def handle(self, *args, **options):
        grupos = {}
        for nombre in ("admin", "normal", "viewer", "cliente"):
            grupos[nombre], _ = Group.objects.get_or_create(name=nombre)

        cuentas = [
            ("admin", config("PASS_ADMIN"), "admin", True, True),
            ("normal", config("PASS_NORMAL"), "normal", False, False),
            ("viewer", config("PASS_VIEWER"), "viewer", False, False),
            ("cliente", config("PASS_CLIENTE"), "cliente", False, False),
        ]
        for username, password, grupo, staff, superuser in cuentas:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": username, "is_staff": staff},
            )
            user.set_password(password)
            user.is_staff = staff
            user.is_superuser = superuser
            user.save()
            user.groups.clear()
            user.groups.add(grupos[grupo])
            Perfil.objects.get_or_create(user=user)

        horarios = [
            (0, time(9, 0), time(18, 0), True),
            (1, time(9, 0), time(18, 0), True),
            (2, time(9, 0), time(18, 0), True),
            (3, time(9, 0), time(18, 0), True),
            (4, time(9, 0), time(18, 0), True),
            (5, time(10, 0), time(14, 0), True),
            (6, time(9, 0), time(18, 0), False),
        ]
        for dia, inicio, fin, activo in horarios:
            HorarioTrabajo.objects.update_or_create(
                dia_semana=dia,
                defaults={
                    "hora_inicio": inicio,
                    "hora_fin": fin,
                    "intervalo_minutos": 60,
                    "activo": activo,
                },
            )

        self.stdout.write(self.style.SUCCESS("Usuarios y horarios listos."))
