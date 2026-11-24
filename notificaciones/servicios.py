from django.utils import timezone
"""Crear notificaciones sin repetirlas, y generar las que dependen del estado de las motos."""
import hashlib
import logging
import time

from .models import Notificacion

logger = logging.getLogger(__name__)
CADA_SEGUNDOS = 10 * 60  # cada cuánto se revisan las motos de una persona mientras navega


def notificar(usuario, clave, titulo, texto="", url="", tipo=Notificacion.Tipo.GENERAL):
    """Crea el aviso si esa persona aún no lo tiene (misma clave). Devuelve la notificación nueva o None."""
    if not usuario or not usuario.pk:
        return None
    notif, creada = Notificacion.objects.get_or_create(
        usuario=usuario, clave=clave[:160],
        defaults={"titulo": titulo[:120], "texto": texto[:300], "url": url[:300], "tipo": tipo},
    )
    return notif if creada else None


def avisar_admins(clave, titulo, texto=""):
    """Avisa a los admins activos de un registro nuevo, con enlace a la consola. Nunca rompe el registro."""
    try:
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        url = reverse("consola:inicio")
        for admin_ in get_user_model().objects.filter(is_staff=True, is_active=True):
            notificar(admin_, clave, titulo, texto, url)
    except Exception:
        logger.exception("No se pudo avisar a los admins (%s)", clave)


def _lista_corta(nombres, maximo=3):
    if len(nombres) <= maximo:
        return ", ".join(nombres)
    return f"{', '.join(nombres[:maximo])} y {len(nombres) - maximo} más"


def _en_dias(dias):
    if dias is None:
        return "sin fecha"
    if dias < 0:
        return "vencido"
    return "hoy" if dias == 0 else f"en {dias} día{'s' if dias != 1 else ''}"


def generar_para(usuario):
    """Avisos de mantenimiento y documentos de las motos del usuario (agrupados por moto)."""
    from garaje.avisos import url_talleres
    from garaje.plan import calcular_plan

    perfil = getattr(usuario, "motociclista", None)
    if not perfil:
        return
    hoy = timezone.localdate()
    from domiciliarios.intensivo import precargar_trabajo
    motos = list(perfil.motos.select_related("linea", "linea__marca"))
    precargar_trabajo(motos)
    for moto in motos:
        plan = calcular_plan(moto)
        ajustes = {a.tarea_id: a for a in moto.ajustes.select_related("tarea")}
        # Mismo criterio que la agenda: "Toca ya" = rojo (vencido o urgente), "Se acerca" = amarillo.
        for estado, titulo, lista in (("vencido", "Toca ya", plan.urgentes), ("pronto", "Se acerca", plan.pronto)):
            # Lo que la persona pospuso no vuelve a avisar hasta la fecha elegida.
            tareas = [t for t in lista if not (t.tarea.pk in ajustes and ajustes[t.tarea.pk].pospuesta)]
            if not tareas:
                continue
            # La firma cambia si cambia la lista o si se registra un mantenimiento: entonces vuelve a avisar.
            firma = hashlib.sha1("|".join(f"{t.tarea.pk}:{t.ultimo_km}" for t in tareas).encode()).hexdigest()[:12]
            n = len(tareas)
            plural = "s" if n != 1 else ""
            # Moto de trabajo (TallerYa Ruta): el domiciliario piensa en días, no en km
            nombres = ([f"{t.tarea.nombre} ({'toca ya' if t.estado == 'vencido' else _en_dias(t.dias_para)})" for t in tareas] if getattr(plan, "de_trabajo", False)
                       else [t.tarea.nombre for t in tareas])
            notificar(
                usuario, f"plan:{moto.pk}:{estado}:{firma}",
                f"{titulo}: {n} mantenimiento{plural} de tu {moto}",
                _lista_corta(nombres),
                url_talleres([t.tarea.servicio_id for t in tareas], moto), Notificacion.Tipo.MANTENIMIENTO,
            )
        for a in ajustes.values():
            if a.recordatorio_pendiente and a.recordar_el <= hoy:
                notificar(usuario, f"recordar:{moto.pk}:{a.tarea_id}:{a.recordar_el}", f"Recordatorio: {a.tarea.nombre}",
                          f"Lo pediste para hoy · {moto}", url_talleres([a.tarea.servicio_id], moto),
                          Notificacion.Tipo.MANTENIMIENTO)
                a.recordado = True
                a.save(update_fields=["recordado"])
        from garaje.pico_placa import aviso_pendiente
        if pyp := aviso_pendiente(moto):
            clave, titulo, texto = pyp
            notificar(usuario, clave, titulo, texto, f"{moto.get_absolute_url()}#pico-placa", Notificacion.Tipo.GENERAL)
        # SOAT y técnico-mecánica: 30, 15 y 3 días antes y al vencer (mismas claves que el comando avisar_vencimientos).
        from garaje.avisos import avisos_documentos
        for a in avisos_documentos(moto, hoy):
            notificar(usuario, a["clave"], a["titulo"], a["texto"], a["url"], Notificacion.Tipo.DOCUMENTO)


def generar_si_toca(request):
    """Se llama al navegar: revisa las motos como mucho cada 10 minutos por sesión."""
    ahora = time.time()
    if ahora - request.session.get("notif_revisadas", 0) < CADA_SEGUNDOS:
        return
    request.session["notif_revisadas"] = ahora
    try:
        generar_para(request.user)
    except Exception:  # un aviso nunca debe romper la página, pero queda en el log para corregirlo
        logger.exception("No se pudieron generar las notificaciones de %s", request.user.pk)


def contexto(request):
    """Procesador de contexto: cantidad de notificaciones sin leer para la campanita."""
    from consola.ajustes import sin_modulos_apagados
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}
    generar_si_toca(request)
    return {"notificaciones_sin_leer": sin_modulos_apagados(Notificacion.objects.filter(usuario=usuario, leida=False)).count(),
            "notificaciones_urgentes": contar_urgentes(usuario)}


def contar_urgentes(usuario):
    """Avisos sin leer en rojo (campana): documento vencido o urgente, pico y placa de hoy o mantenimiento "Toca ya"."""
    from django.db.models import Q
    from garaje.avisos import es_urgente

    hoy = timezone.localdate()
    claves = Notificacion.objects.filter(usuario=usuario, leida=False).filter(
        Q(clave__startswith="doc:") | Q(clave__startswith="pyp:") | Q(clave__contains=":vencido:")
    ).values_list("clave", flat=True)
    return sum(1 for c in claves if es_urgente(c, hoy))
