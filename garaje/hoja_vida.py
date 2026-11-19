"""Hoja de vida verificada: códigos de un solo uso para el taller y enlaces públicos revocables.

Privacidad: con el código vigente el taller registra verificado de una vez. Por placa (garaje.servicio_taller) solo ve
marca/línea y nada queda en la hoja de vida hasta que el dueño lo confirma.
"""
import re
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import CodigoServicio, EnlaceHojaVida, LecturaKm, RegistroServicio

ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin 0/O, 1/I/L para dictarlo sin errores
LARGO_CODIGO = 6
MINUTOS_CODIGO = 30


class CodigoInvalido(Exception):
    """El código no existe, ya se usó o caducó."""


def normalizar(texto):
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def generar_codigo(moto, registro=None):
    """Código nuevo para esta moto; anula los anteriores sin usar (solo hay uno vivo a la vez)."""
    ahora = timezone.now()
    moto.codigos_servicio.filter(usado__isnull=True, vence__gt=ahora).update(vence=ahora)
    while True:
        codigo = "".join(secrets.choice(ALFABETO) for _ in range(LARGO_CODIGO))
        if not CodigoServicio.objects.filter(codigo=codigo).exists():
            return CodigoServicio.objects.create(moto=moto, codigo=codigo, registro=registro,
                                                 vence=ahora + timedelta(minutes=MINUTOS_CODIGO))


def codigo_para(moto, registro=None):
    """El código vigente (reutilizado, sin crear uno cada vez) o uno nuevo; si se pide para un registro pendiente,
    queda ligado a él para que el taller verifique ese mismo registro."""
    codigo = codigo_vigente(moto)
    if not codigo:
        return generar_codigo(moto, registro)
    if registro and codigo.registro_id != registro.pk:
        codigo.registro = registro
        codigo.save(update_fields=["registro"])
    return codigo


def ligar_codigo_pendiente(registro):
    """Si el dueño ya tenía un código vigente sin registro (lo sacó al elegir el taller) y el registro es pendiente,
    se ligan: así el taller verifica este mismo registro."""
    if registro.estado_verificacion == "pendiente":
        registro.moto.codigos_servicio.filter(usado__isnull=True, vence__gt=timezone.now(),
                                              registro__isnull=True).update(registro=registro)


def codigo_vigente(moto):
    return moto.codigos_servicio.filter(usado__isnull=True, vence__gt=timezone.now()).order_by("-creado").first()


def buscar_codigo(texto):
    """CodigoServicio vigente para ese texto, o None."""
    codigo = normalizar(texto)
    if len(codigo) != LARGO_CODIGO:
        return None
    return (CodigoServicio.objects.select_related("moto", "moto__linea", "moto__linea__marca")
            .filter(codigo=codigo, usado__isnull=True, vence__gt=timezone.now()).first())


DIAS_EMPATE = 10  # un registro pendiente con el mismo taller dentro de ±10 días se toma como el mismo servicio


def desde_mantenimiento(m, costo=None):
    """La hoja de vida es la única fuente de historial: cada mantenimiento del plan tiene su registro (sin verificar).
    No lo repite: si ya está enlazado lo devuelve, y si hay uno igual sin enlazar, lo enlaza."""
    registro = RegistroServicio.objects.filter(mantenimiento=m).first()
    if not registro:
        nombre = m.tarea.nombre[:300]
        registro = RegistroServicio.objects.filter(moto=m.moto, mantenimiento__isnull=True, fecha=m.fecha, km=m.km,
                                                   servicios=nombre).first()
        if registro:
            registro.mantenimiento = m
            registro.save(update_fields=["mantenimiento"])
        else:
            registro = RegistroServicio.objects.create(moto=m.moto, fecha=m.fecha, km=m.km, servicios=nombre,
                                                       notas=m.notas[:300], taller=m.taller,
                                                       taller_otro=m.taller_otro, mantenimiento=m)
            ligar_codigo_pendiente(registro)
    if costo is not None and registro.costo != costo:
        registro.costo = costo
        registro.save(update_fields=["costo"])
    return registro


def registrar_propio(moto, registro, tarea=None):
    """Servicio agregado por el dueño en la hoja de vida. Si eligió qué mantenimiento del plan cubre, el plan se pone
    al día igual que desde la ficha (y el registro queda enlazado a ese mantenimiento, una sola vez)."""
    from .models import AjusteTarea, Mantenimiento
    registro.moto = moto
    if not tarea:
        registro.save()
        ligar_codigo_pendiente(registro)
        return registro
    with transaction.atomic():
        m = Mantenimiento.objects.create(moto=moto, tarea=tarea, km=registro.km, fecha=registro.fecha,
                                         taller=registro.taller, taller_otro=registro.taller_otro,
                                         notas=registro.notas[:200])
        AjusteTarea.objects.filter(moto=moto, tarea=tarea).delete()
        enlazado = desde_mantenimiento(m)  # ya lo creó la señal; se completa con lo que escribió el dueño
        enlazado.servicios = registro.servicios or enlazado.servicios
        enlazado.costo, enlazado.notas = registro.costo, registro.notas
        enlazado.save()
    return enlazado


def eliminar_propio(moto, pk):
    """Borra un registro propio (lo verificado no). Si viene del plan, también se quita del plan."""
    registro = moto.hoja_vida.filter(pk=pk, verificado=False).select_related("mantenimiento").first()
    if not registro:
        return False
    with transaction.atomic():
        m = registro.mantenimiento
        registro.delete()
        if m:
            m.delete()
    return True


def registrar_verificado(taller, codigo, *, fecha, km, servicios, notas="", costo=None):
    """Crea un registro verificado con el código del dueño y lo gasta. Lanza CodigoInvalido si no sirve."""
    with transaction.atomic():
        obj = CodigoServicio.objects.select_for_update().filter(
            codigo=normalizar(codigo), usado__isnull=True, vence__gt=timezone.now()).first()
        # Actualización condicional: solo un envío gasta el código aunque lleguen dos a la vez
        if not obj or not taller or not CodigoServicio.objects.filter(pk=obj.pk, usado__isnull=True).update(
                usado=timezone.now()):
            raise CodigoInvalido("El código no es válido o ya caducó. Pídele al motero uno nuevo.")
        obj.refresh_from_db()
        # Si el dueño ya lo había anotado (p. ej. "Ya le hice este mantenimiento" con este taller), ese registro
        # pasa a verificado con los datos del taller en vez de quedar dos veces.
        # 1) el registro pendiente ligado al código; 2) uno pendiente con este taller en fecha cercana; 3) uno nuevo.
        ligado = obj.registro if obj.registro_id and not obj.registro.verificado and obj.registro.moto_id == obj.moto_id else None
        registro = ligado or (RegistroServicio.objects.select_for_update()
                              .filter(moto=obj.moto, taller=taller, verificado=False,
                                      fecha__range=(fecha - timedelta(days=DIAS_EMPATE), fecha + timedelta(days=DIAS_EMPATE)))
                              .order_by("-fecha", "-pk").first()) or RegistroServicio(moto=obj.moto)
        registro.fecha, registro.km, registro.servicios, registro.taller = fecha, km, servicios, taller
        registro.notas = notas or registro.notas
        registro.costo = costo if costo is not None else registro.costo
        registro.taller_otro = ""
        registro.verificado = True
        registro.save()
        moto = obj.moto
        if km > moto.km_actual:  # el taller vio el odómetro: también cuenta como lectura de kilometraje
            LecturaKm.objects.create(moto=moto, km=km, fecha=fecha)
            moto.km_actual = km
            moto.save(update_fields=["km_actual"])
    return registro


def enlace_activo(moto):
    return moto.enlaces_hoja_vida.filter(revocado__isnull=True).order_by("-creado").first()


def crear_enlace(moto):
    return enlace_activo(moto) or EnlaceHojaVida.objects.create(moto=moto)


def revocar_enlaces(moto):
    return moto.enlaces_hoja_vida.filter(revocado__isnull=True).update(revocado=timezone.now())


def placa_enmascarada(placa):
    """ABC12D → A••••D: sirve para reconocerla sin exponerla."""
    placa = (placa or "").strip().upper()
    if len(placa) < 3:
        return "Sin placa"
    return placa[0] + "•" * (len(placa) - 2) + placa[-1]


def resumen(registros):
    verificados = [r for r in registros if r.verificado]
    return {"total": len(registros), "verificados": len(verificados),
            "talleres": sorted({r.taller.nombre for r in verificados if r.taller}
                               | {f"{r.mecanico.nombre} (a domicilio)" for r in verificados if r.mecanico})}
