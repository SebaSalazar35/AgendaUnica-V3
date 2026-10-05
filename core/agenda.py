from datetime import datetime, time, timedelta
from urllib.parse import quote

from django.utils import timezone

from core.models import Bloqueo, HorarioTrabajo, Registro


def _aware(fecha, hora):
    naive = datetime.combine(fecha, hora)
    if timezone.is_naive(naive):
        return timezone.make_aware(naive)
    return naive


def horario_del_dia(fecha):
    return HorarioTrabajo.objects.filter(
        dia_semana=fecha.weekday(),
        activo=True,
    ).first()


def horas_laborales(fecha):
    horario = horario_del_dia(fecha)
    if not horario:
        return []
    return horario.horas()


def reserva_vigente(usuario):
    return (
        Registro.objects.filter(
            usuario=usuario,
            resultado="Aceptado",
            eliminado=False,
            liberada=False,
            fecha_cita__gte=timezone.now(),
        )
        .order_by("fecha_cita")
        .first()
    )


def cita_ocupada(fecha, hora):
    momento = _aware(fecha, hora)
    return Registro.objects.filter(
        fecha_cita=momento,
        resultado="Aceptado",
        eliminado=False,
        liberada=False,
    ).exists()


def hora_bloqueada(fecha, hora):
    momento = _aware(fecha, hora)
    return Bloqueo.objects.filter(fecha_hora=momento).exists()


def hora_disponible(fecha, hora):
    if hora not in horas_laborales(fecha):
        return False
    if cita_ocupada(fecha, hora):
        return False
    if hora_bloqueada(fecha, hora):
        return False
    return True


def reserva_en(fecha, hora):
    momento = _aware(fecha, hora)
    return (
        Registro.objects.filter(
            fecha_cita=momento,
            resultado="Aceptado",
            eliminado=False,
            liberada=False,
        )
        .select_related("usuario")
        .first()
    )


def bloqueo_en(fecha, hora):
    momento = _aware(fecha, hora)
    return Bloqueo.objects.filter(fecha_hora=momento).first()


DIAS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


def armar_semana(inicio=None, dias=7):
    if inicio is None:
        inicio = timezone.localdate()
    semana = []
    for i in range(dias):
        fecha = inicio + timedelta(days=i)
        horas = []
        for hora in horas_laborales(fecha):
            reserva = reserva_en(fecha, hora)
            bloqueo = bloqueo_en(fecha, hora)
            if reserva:
                estado = "ocupada"
            elif bloqueo:
                estado = "bloqueada"
            else:
                estado = "libre"
            horas.append(
                {
                    "hora": hora,
                    "estado": estado,
                    "reserva": reserva,
                    "bloqueo": bloqueo,
                }
            )
        ocupadas = sum(1 for h in horas if h["estado"] == "ocupada")
        semana.append(
            {
                "fecha": fecha,
                "nombre": DIAS_ES[fecha.weekday()],
                "horas": horas,
                "cerrado": len(horas) == 0,
                "atendidas": ocupadas,
            }
        )
    return semana


def lunes_de(fecha):
    return fecha - timedelta(days=fecha.weekday())


def parse_inicio_semana(valor):
    hoy = timezone.localdate()
    if valor:
        try:
            fecha = datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            fecha = hoy
    else:
        fecha = hoy
    return lunes_de(fecha)


def _rango_semana(inicio):
    fin = inicio + timedelta(days=7)
    inicio_dt = timezone.make_aware(datetime.combine(inicio, time.min))
    fin_dt = timezone.make_aware(datetime.combine(fin, time.min))
    return inicio_dt, fin_dt


def estadisticas_semana(inicio):
    inicio_dt, fin_dt = _rango_semana(inicio)
    base = Registro.objects.filter(
        fecha_cita__gte=inicio_dt,
        fecha_cita__lt=fin_dt,
        resultado="Aceptado",
        eliminado=False,
    )
    atendidas = base.filter(liberada=False).count()
    no_show = base.filter(liberada=True).count()
    return {
        "inicio": inicio,
        "fin": inicio + timedelta(days=6),
        "atendidas": atendidas,
        "no_show": no_show,
        "total": atendidas + no_show,
    }


def historial_semanas(referencia, cantidad=8):
    filas = []
    for i in range(cantidad - 1, -1, -1):
        inicio = referencia - timedelta(days=7 * i)
        fila = estadisticas_semana(inicio)
        fila["actual"] = inicio == referencia
        filas.append(fila)
    return filas


def enlace_whatsapp(numero, registro):
    if not numero or not registro.fecha_cita:
        return ""
    cita = timezone.localtime(registro.fecha_cita)
    patente = f" Patente: {registro.patente}." if registro.patente else ""
    servicio = f" Servicio: {registro.servicio}." if registro.servicio else ""
    texto = (
        f"Hola, confirmo mi hora en el taller mecanico el "
        f"{cita.strftime('%d/%m/%Y')} a las {cita.strftime('%H:%M')}. "
        f"Nombre: {registro.nombre}.{patente}{servicio}"
    )
    return f"https://wa.me/{numero}?text={quote(texto)}"
