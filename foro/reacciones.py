"""Reacciones del foro: conteos por mensaje, cambiar/quitar la propia y aviso agrupado al autor."""
from django.db.models import Count
from django.utils import timezone

from notificaciones.models import Notificacion

from .models import Reaccion

MOTIVOS_REPORTE = [
    ("inapropiado", "Contenido inapropiado u ofensivo"),
    ("spam", "Spam o publicidad"),
    ("peligroso", "Información peligrosa o falsa"),
    ("otro", "Otro"),
]


def opciones():
    return [(clave, Reaccion.EMOJI[clave], nombre) for clave, nombre in Reaccion.Tipo.choices]


def _quienes(nombres, total, mia):
    """Texto al pasar el mouse: "Tú, Camila y 2 más"."""
    lista = (["Tú"] if mia else []) + nombres
    if len(lista) > 3:
        return f"{', '.join(lista[:3])} y {total - 3} más"
    return " y ".join([", ".join(lista[:-1]), lista[-1]]) if len(lista) > 1 else (lista[0] if lista else "")


def resumen(conteos, mia, nombres=None):
    """Lista para la plantilla: solo las reacciones usadas, en el orden del selector, con quiénes reaccionaron."""
    nombres = nombres or {}
    return [{"clave": c, "emoji": e, "nombre": n, "n": conteos.get(c, 0), "mia": c == mia,
             "quienes": _quienes(nombres.get(c, []), conteos.get(c, 0), c == mia)}
            for c, e, n in opciones() if conteos.get(c)]


def _agrupar(filas, usuario_id):
    """filas: (clave_obj, tipo, usuario_id, nombre, taller). Devuelve {clave_obj: (conteos, nombres, mia)}."""
    datos = {}
    for clave, tipo, u_id, nombre, taller in filas:
        conteos, nombres, mia = datos.setdefault(clave, ({}, {}, [""]))
        conteos[tipo] = conteos.get(tipo, 0) + 1
        if u_id == usuario_id:
            mia[0] = tipo
        else:
            nombres.setdefault(tipo, []).append(taller or nombre or "Motociclista")
    return datos


CAMPOS = ("tipo", "usuario_id", "usuario__first_name", "usuario__taller__nombre")


def adjuntar(pregunta, respuestas, usuario):
    """Pone .reacciones_lista y .reaccion_mia en la pregunta y en cada respuesta (una consulta)."""
    from django.db.models import Q
    filas = (Reaccion.objects.filter(Q(pregunta=pregunta) | Q(respuesta__pregunta=pregunta))
             .values_list("pregunta_id", "respuesta_id", *CAMPOS).order_by("creado"))
    datos = _agrupar(((("p", p) if p else ("r", r), *resto) for p, r, *resto in filas), usuario.pk)
    for clave, obj in [(("p", pregunta.pk), pregunta)] + [(("r", r.pk), r) for r in respuestas]:
        conteos, nombres, mia = datos.get(clave, ({}, {}, [""]))
        obj.reaccion_mia = mia[0]
        obj.reacciones_lista = resumen(conteos, mia[0], nombres)


def reaccionar(usuario, objeto, tipo_objeto, tipo):
    """Pone, cambia o quita (si repite la misma) la reacción. Devuelve True si quedó una reacción nueva o distinta."""
    filtro = {"usuario": usuario, tipo_objeto: objeto}
    actual = Reaccion.objects.filter(**filtro).first()
    if actual and actual.tipo == tipo:
        actual.delete()
        return False
    if actual:
        actual.tipo = tipo
        actual.save(update_fields=["tipo"])
    else:
        Reaccion.objects.create(tipo=tipo, **filtro)
    return True


def estado(objeto, tipo_objeto, usuario):
    filas = objeto.reacciones.values_list(*CAMPOS).order_by("creado")
    conteos, nombres, mia = _agrupar((("x", *f) for f in filas), usuario.pk).get("x", ({}, {}, [""]))
    objeto.reaccion_mia, objeto.reacciones_lista = mia[0], resumen(conteos, mia[0], nombres)
    return objeto


def avisar_autor(objeto, tipo_objeto, usuario):
    """Un solo aviso por mensaje que se actualiza: "A 3 personas les gustó tu respuesta". Nunca uno por reacción."""
    autor = objeto.autor
    reacciones = objeto.reacciones.exclude(usuario=autor).select_related("usuario")
    total = reacciones.count()
    if not total:
        return
    tipos = set(reacciones.values_list("tipo", flat=True))
    que = "tu pregunta" if tipo_objeto == "pregunta" else "tu respuesta"
    if total == 1:
        from .menciones import nombre_publico
        quien = nombre_publico(usuario)
        titulo = f"A {quien} le gustó {que}" if tipos == {"gusta"} else f"{quien} reaccionó a {que}"
    else:
        titulo = f"A {total} personas les gustó {que}" if tipos == {"gusta"} else f"{total} personas reaccionaron a {que}"
    pregunta = objeto if tipo_objeto == "pregunta" else objeto.pregunta
    texto = " ".join(Reaccion.EMOJI[t] for t, _ in Reaccion.Tipo.choices if t in tipos) + f" · {pregunta.titulo}"
    Notificacion.objects.update_or_create(
        usuario=autor, clave=f"foro-reacciones:{tipo_objeto[0]}{objeto.pk}",
        defaults={"titulo": titulo[:120], "texto": texto[:300], "url": objeto.get_absolute_url()[:300],
                  "tipo": Notificacion.Tipo.FORO, "leida": False, "creada": timezone.now()},
    )
