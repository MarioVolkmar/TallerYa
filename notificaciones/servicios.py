from django.utils import timezone
"""Crear notificaciones sin repetirlas, y generar las que dependen del estado de las motos."""
import hashlib
import time

from .models import Notificacion

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


def _lista_corta(nombres, maximo=3):
    if len(nombres) <= maximo:
        return ", ".join(nombres)
    return f"{', '.join(nombres[:maximo])} y {len(nombres) - maximo} más"


def generar_para(usuario):
    """Avisos de mantenimiento y documentos de las motos del usuario (agrupados por moto)."""
    from garaje.plan import calcular_plan

    perfil = getattr(usuario, "motociclista", None)
    if not perfil:
        return
    hoy = timezone.localdate()
    for moto in perfil.motos.select_related("linea", "linea__marca"):
        plan = calcular_plan(moto)
        ajustes = {a.tarea_id: a for a in moto.ajustes.all()}
        for estado, titulo in (("vencido", "Toca ya"), ("pronto", "Se acerca")):
            # Lo que la persona pospuso no vuelve a avisar hasta la fecha elegida.
            tareas = [t for t in plan.tareas if t.estado == estado and not (t.tarea.pk in ajustes and ajustes[t.tarea.pk].pospuesta)]
            if not tareas:
                continue
            # La firma cambia si cambia la lista o si se registra un mantenimiento: entonces vuelve a avisar.
            firma = hashlib.sha1("|".join(f"{t.tarea.pk}:{t.ultimo_km}" for t in tareas).encode()).hexdigest()[:12]
            n = len(tareas)
            plural = "s" if n != 1 else ""
            notificar(
                usuario, f"plan:{moto.pk}:{estado}:{firma}",
                f"{titulo}: {n} mantenimiento{plural} de tu {moto}",
                _lista_corta([t.tarea.nombre for t in tareas]),
                f"{moto.get_absolute_url()}#plan", Notificacion.Tipo.MANTENIMIENTO,
            )
        for a in ajustes.values():
            if a.recordatorio_pendiente and a.recordar_el <= hoy:
                notificar(usuario, f"recordar:{moto.pk}:{a.tarea_id}:{a.recordar_el}", f"Recordatorio: {a.tarea.nombre}",
                          f"Lo pediste para hoy · {moto}", f"{moto.get_absolute_url()}#plan", Notificacion.Tipo.MANTENIMIENTO)
                a.recordado = True
                a.save(update_fields=["recordado"])
        for doc in moto.documentos():
            if doc["estado"] == "vencido":
                titulo = f"Tu {doc['nombre']} está vencido"
            elif doc["estado"] == "pronto":
                cuando = "hoy" if doc["dias"] == 0 else f"en {doc['dias']} días"
                titulo = f"Tu {doc['nombre']} vence {cuando}"
            else:
                continue
            notificar(
                usuario, f"doc:{moto.pk}:{doc['clave']}:{doc['estado']}:{doc['vence']}", titulo,
                f"{moto} · vence el {doc['vence']:%d/%m/%Y}", moto.get_absolute_url(), Notificacion.Tipo.DOCUMENTO,
            )


def generar_si_toca(request):
    """Se llama al navegar: revisa las motos como mucho cada 10 minutos por sesión."""
    ahora = time.time()
    if ahora - request.session.get("notif_revisadas", 0) < CADA_SEGUNDOS:
        return
    request.session["notif_revisadas"] = ahora
    try:
        generar_para(request.user)
    except Exception:  # un aviso nunca debe romper la página
        pass


def contexto(request):
    """Procesador de contexto: cantidad de notificaciones sin leer para la campanita."""
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        return {}
    generar_si_toca(request)
    return {"notificaciones_sin_leer": Notificacion.objects.filter(usuario=usuario, leida=False).count()}
