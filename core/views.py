from datetime import datetime, timedelta

from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.agenda import (
    armar_semana,
    cita_ocupada,
    enlace_whatsapp,
    estadisticas_semana,
    historial_semanas,
    hora_disponible,
    horas_laborales,
    parse_inicio_semana,
    reserva_vigente,
)
from core.models import Bloqueo, HorarioTrabajo, Perfil, Registro
from core.patente import normalizar_patente, patente_valida
from core.roles import a_donde_va, requiere_rol
from solucion import CUPOS, decidir


def cupos_para(excepto=None):
    # Cuento los aceptados. Un rechazo no ocupa cupo.
    ocupados = 0
    for r in Registro.objects.filter(
        resultado="Aceptado",
        eliminado=False,
        liberada=False,
    ):
        if excepto is not None and r.pk == excepto:
            continue
        ocupados = ocupados + 1
    libres = CUPOS - ocupados
    if libres < 0:
        return 0
    return libres


def _perfil(user):
    perfil, _ = Perfil.objects.get_or_create(user=user)
    return perfil


def _whatsapp(registro):
    return enlace_whatsapp(config("WHATSAPP_SALON", default=""), registro)


def inicio(request):
    if request.user.is_authenticated:
        return redirect(a_donde_va(request.user))
    return redirect("login")


def vista_login(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", ""),
        )
        if user:
            login(request, user)
            return redirect("inicio")
        messages.error(request, "Usuario o contrasena incorrectos.")
    return render(request, "login.html")


def vista_logout(request):
    logout(request)
    return redirect("login")


def registro_cuenta(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        if not username or not password or not nombre:
            error = "Completa usuario, contrasena y nombre."
        elif User.objects.filter(username=username).exists():
            error = "Ese usuario ya existe."
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombre,
            )
            grupo, _ = Group.objects.get_or_create(name="cliente")
            user.groups.add(grupo)
            Perfil.objects.create(user=user, telefono=telefono)
            login(request, user)
            return redirect("calendario")
    return render(request, "registro.html", {"error": error})


@requiere_rol("cliente")
def calendario(request):
    perfil = _perfil(request.user)
    vigente = reserva_vigente(request.user)
    agendada = None
    agendada_pk = request.GET.get("agendada")
    if agendada_pk:
        agendada = Registro.objects.filter(
            pk=agendada_pk,
            usuario=request.user,
            resultado="Aceptado",
            eliminado=False,
            liberada=False,
        ).first()
    return render(
        request,
        "calendario.html",
        {
            "semana": armar_semana(),
            "nombre": request.user.first_name or request.user.username,
            "telefono": perfil.telefono,
            "reserva_actual": vigente,
            "agendada": agendada,
            "whatsapp": _whatsapp(agendada) if agendada else "",
        },
    )


@requiere_rol("cliente")
@require_POST
def reservar(request):
    perfil = _perfil(request.user)
    vigente = reserva_vigente(request.user)
    if vigente:
        messages.error(
            request,
            "Ya tienes una hora vigente. Liberarla antes de tomar otra.",
        )
        return redirect("calendario")

    fecha_txt = request.POST.get("fecha", "")
    hora_txt = request.POST.get("hora", "")
    try:
        fecha = datetime.strptime(fecha_txt, "%Y-%m-%d").date()
        hora = datetime.strptime(hora_txt, "%H:%M").time()
    except ValueError:
        messages.error(request, "Elige un dia y una hora del calendario.")
        return redirect("calendario")

    if fecha < timezone.localdate():
        messages.error(request, "No se puede agendar en un dia pasado.")
        return redirect("calendario")

    if not hora_disponible(fecha, hora):
        messages.error(request, "Esa hora ya no esta disponible.")
        return redirect("calendario")

    nombre = request.POST.get("nombre", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    patente = normalizar_patente(request.POST.get("patente", ""))
    servicio = request.POST.get("servicio", "").strip()
    if not patente_valida(patente):
        messages.error(
            request,
            "La patente no es valida. Usa el formato chileno ABCD12 o AB1234.",
        )
        return redirect("calendario")
    inasistencias = perfil.inasistencias
    cupos = 1
    resultado = decidir(inasistencias, cupos)
    momento = timezone.make_aware(datetime.combine(fecha, hora))
    registro = Registro.objects.create(
        usuario=request.user,
        nombre=nombre or request.user.first_name or request.user.username,
        telefono=telefono or perfil.telefono,
        patente=patente,
        servicio=servicio,
        inasistencias=inasistencias,
        resultado=resultado,
        fecha_cita=momento,
    )
    if telefono:
        perfil.telefono = telefono
        perfil.save()
    if resultado == "Aceptado":
        return redirect(f"{reverse('calendario')}?agendada={registro.pk}")
    messages.warning(request, resultado)
    return redirect("calendario")


@requiere_rol("cliente")
@require_POST
def cancelar_propia(request, pk):
    registro = get_object_or_404(
        Registro,
        pk=pk,
        usuario=request.user,
        resultado="Aceptado",
        eliminado=False,
        liberada=False,
    )
    registro.liberada = True
    registro.motivo_liberacion = "cliente libero su hora"
    registro.save()
    messages.success(request, "Liberaste tu hora. Ya puedes tomar otra.")
    return redirect("calendario")


@requiere_rol("cliente")
def mis_horas(request):
    reservas = []
    for registro in Registro.objects.filter(usuario=request.user, eliminado=False):
        reservas.append(
            {
                "registro": registro,
                "whatsapp": _whatsapp(registro)
                if registro.resultado == "Aceptado" and not registro.liberada
                else "",
            }
        )
    return render(request, "mis_horas.html", {"reservas": reservas})


def _volver_panel(request):
    inicio = parse_inicio_semana(
        request.POST.get("semana") or request.GET.get("semana")
    )
    return redirect(f"{reverse('panel')}?semana={inicio.isoformat()}")


@login_required(login_url="login")
def lista(request):
    registros = Registro.objects.filter(eliminado=False)
    return render(request, "lista.html", {"registros": registros})


@requiere_rol("admin", "normal")
def crear(request):
    error = None
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        try:
            inasistencias = int(request.POST.get("inasistencias", ""))
        except ValueError:
            error = "Las inasistencias deben ser un numero entero."
        else:
            patente = normalizar_patente(request.POST.get("patente", ""))
            if patente and not patente_valida(patente):
                error = "La patente no es valida. Usa ABCD12 o AB1234."
            else:
                resultado = decidir(inasistencias, cupos_para())
                Registro.objects.create(
                    nombre=nombre,
                    telefono=request.POST.get("telefono", "").strip(),
                    patente=patente,
                    servicio=request.POST.get("servicio", "").strip(),
                    inasistencias=inasistencias,
                    resultado=resultado,
                )
                return redirect("lista")
    return render(request, "form.html", {"accion": "Crear", "error": error})


@requiere_rol("admin")
def editar(request, pk):
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    error = None
    if request.method == "POST":
        try:
            inasistencias = int(request.POST.get("inasistencias", ""))
        except ValueError:
            error = "Las inasistencias deben ser un numero entero."
        else:
            patente = normalizar_patente(request.POST.get("patente", ""))
            if patente and not patente_valida(patente):
                error = "La patente no es valida. Usa ABCD12 o AB1234."
            else:
                reg.nombre = request.POST.get("nombre", "").strip()
                reg.telefono = request.POST.get("telefono", "").strip()
                reg.patente = patente
                reg.servicio = request.POST.get("servicio", "").strip()
                reg.inasistencias = inasistencias
                reg.resultado = decidir(inasistencias, cupos_para(excepto=reg.pk))
                reg.save()
                return redirect("lista")
    return render(
        request,
        "form.html",
        {"accion": "Editar", "registro": reg, "error": error},
    )


@requiere_rol("admin")
def eliminar(request, pk):
    reg = get_object_or_404(Registro, pk=pk, eliminado=False)
    if request.method == "POST":
        reg.soft_delete()
        return redirect("lista")
    return render(request, "confirmar.html", {"registro": reg})


@requiere_rol("admin")
def panel(request):
    inicio = parse_inicio_semana(request.GET.get("semana"))
    stats = estadisticas_semana(inicio)
    return render(
        request,
        "panel.html",
        {
            "semana": armar_semana(inicio),
            "inicio_semana": inicio,
            "semana_anterior": inicio - timedelta(days=7),
            "semana_siguiente": inicio + timedelta(days=7),
            "semana_actual": parse_inicio_semana(None),
            "stats": stats,
            "historial": historial_semanas(inicio),
            "reservas": Registro.objects.filter(
                resultado="Aceptado",
                eliminado=False,
                liberada=False,
                fecha_cita__gte=timezone.make_aware(
                    datetime.combine(inicio, datetime.min.time())
                ),
                fecha_cita__lt=timezone.make_aware(
                    datetime.combine(inicio + timedelta(days=7), datetime.min.time())
                ),
            ).order_by("fecha_cita"),
        },
    )


@requiere_rol("admin")
def horarios(request):
    if request.method == "POST":
        for dia, nombre in HorarioTrabajo.DIAS:
            activo = request.POST.get(f"activo_{dia}") == "on"
            try:
                inicio = datetime.strptime(
                    request.POST.get(f"inicio_{dia}", "09:00"), "%H:%M"
                ).time()
                fin = datetime.strptime(
                    request.POST.get(f"fin_{dia}", "18:00"), "%H:%M"
                ).time()
                intervalo = int(request.POST.get(f"intervalo_{dia}", "60"))
            except ValueError:
                messages.error(request, f"Revisa el horario del {nombre}.")
                return redirect("horarios")
            HorarioTrabajo.objects.update_or_create(
                dia_semana=dia,
                defaults={
                    "hora_inicio": inicio,
                    "hora_fin": fin,
                    "intervalo_minutos": intervalo,
                    "activo": activo,
                },
            )
        messages.success(request, "Horarios de trabajo actualizados.")
        return redirect("horarios")

    actuales = {h.dia_semana: h for h in HorarioTrabajo.objects.all()}
    filas = []
    for dia, nombre in HorarioTrabajo.DIAS:
        filas.append({"dia": dia, "nombre": nombre, "horario": actuales.get(dia)})
    return render(request, "horarios.html", {"filas": filas})


@requiere_rol("admin")
@require_POST
def liberar(request, pk):
    registro = get_object_or_404(
        Registro,
        pk=pk,
        resultado="Aceptado",
        eliminado=False,
        liberada=False,
    )
    registro.liberar_por_noshow()
    messages.success(
        request,
        f"Se libero la hora de {registro.nombre} por no-show. El cliente suma 1 inasistencia.",
    )
    return _volver_panel(request)


@requiere_rol("admin")
@require_POST
def bloquear_hora(request):
    fecha_txt = request.POST.get("fecha", "")
    hora_txt = request.POST.get("hora", "")
    motivo = request.POST.get("motivo", "").strip() or "Bloqueo manual"
    try:
        fecha = datetime.strptime(fecha_txt, "%Y-%m-%d").date()
        hora = datetime.strptime(hora_txt, "%H:%M").time()
    except ValueError:
        messages.error(request, "No se pudo bloquear esa hora.")
        return _volver_panel(request)
    if cita_ocupada(fecha, hora):
        messages.error(request, "Esa hora ya esta tomada. Liberarla primero.")
        return _volver_panel(request)
    if hora not in horas_laborales(fecha):
        messages.error(request, "Esa hora no esta en el horario del taller.")
        return _volver_panel(request)
    Bloqueo.objects.get_or_create(
        fecha_hora=timezone.make_aware(datetime.combine(fecha, hora)),
        defaults={"motivo": motivo},
    )
    messages.success(request, "Hora bloqueada.")
    return _volver_panel(request)


@requiere_rol("admin")
@require_POST
def desbloquear_hora(request, pk):
    bloqueo = get_object_or_404(Bloqueo, pk=pk)
    bloqueo.delete()
    messages.success(request, "Hora liberada. Ya puede tomarla otro vehiculo.")
    return _volver_panel(request)


@login_required(login_url="login")
def resumen(request):
    return redirect("inicio")
