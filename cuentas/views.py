from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cupones.models import Cupon, Motociclista
from cupones.servicios import CuponNoDisponible, reclamar_regalo_mensual
from garaje.plan import calcular_plan

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from talleres.forms import RegistroTallerForm
from talleres.models import Taller

from . import roles
from .avatares import PREDISENADOS, html_avatar, svg_predisenado
from . import google
from .forms import AvatarForm, CelularForm, CuentaTallerForm, RegistroForm, foto_cuadrada
from .models import Perfil, Suscripcion

User = get_user_model()


def registro(request):
    """Crear cuenta: primero se elige el tipo (motero o taller)."""
    if request.user.is_authenticated:
        return redirect("cuentas:mi_cuenta")
    tipo = request.GET.get("tipo")
    if tipo == "taller":
        return _registro_taller(request)
    if tipo != "motero" and request.method != "POST":
        return render(request, "cuentas/registro_elegir.html")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=d["email"], email=d["email"], password=d["password1"], first_name=d["nombre"],
            )
            moto = form.motociclista_existente or Motociclista(celular=d["celular"], nombre=d["nombre"])
            if not moto.pk and (ref := request.session.get("ref")):
                moto.referido_por = Motociclista.objects.filter(codigo_referido=ref).first()
            moto.usuario = usuario
            moto.save()
        login(request, usuario)
        messages.success(request, f"¡Bienvenido a TallerYa, {d['nombre']}!")
        siguiente = request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(siguiente, {request.get_host()}, require_https=request.is_secure()):
            return redirect(siguiente)
        return redirect("cuentas:mi_cuenta")
    return render(request, "cuentas/registro.html", {"form": form})


def _registro_taller(request):
    """Cuenta del taller + datos del negocio. El taller queda en revisión hasta que un administrador lo apruebe."""
    cuenta = CuentaTallerForm(request.POST or None)
    negocio = RegistroTallerForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and cuenta.is_valid() and negocio.is_valid():
        d = cuenta.cleaned_data
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=d["email"], email=d["email"], password=d["password1"],
                first_name=negocio.cleaned_data["responsable"],
            )
            taller = negocio.save(commit=False)
            taller.usuario = usuario
            taller.activo = False
            taller.save()
            negocio.save_m2m()
        login(request, usuario)
        messages.success(request, "¡Cuenta creada! Revisaremos tu taller y lo publicaremos pronto.")
        return redirect("cuentas:mi_cuenta")
    return render(request, "cuentas/registro_taller.html", {"cuenta": cuenta, "negocio": negocio})


def historial_servicios(moto_perfil, limite=200):
    """Servicios tomados por el motero: mantenimientos registrados, cupones canjeados y citas pedidas a talleres."""
    from garaje.models import Mantenimiento
    from talleres.models import SolicitudCita
    from talleres.utils import normalizar_celular

    eventos = []
    for m in (Mantenimiento.objects.filter(moto__motociclista=moto_perfil)
              .select_related("tarea", "taller", "moto", "moto__linea", "moto__linea__marca")[:limite]):
        eventos.append({"fecha": m.fecha, "tipo": "mantenimiento", "titulo": m.tarea.nombre, "moto": str(m.moto),
                        "sistema": m.tarea.get_pieza_display(),
                        "detalle": f"{m.moto} · {m.km:,} km".replace(",", "."), "lugar": m.donde,
                        "url": m.taller.get_absolute_url() if m.taller else "", "taller": m.taller})
    for c in (moto_perfil.codigos.filter(canjeado_en__isnull=False)
              .select_related("cupon", "canjeado_taller").order_by("-canjeado_en")[:limite]):
        eventos.append({"fecha": timezone.localtime(c.canjeado_en).date(), "tipo": "cupon", "titulo": c.cupon.titulo, "moto": "",
                        "detalle": "Cupón canjeado", "lugar": str(c.canjeado_taller or ""),
                        "url": c.canjeado_taller.get_absolute_url() if c.canjeado_taller else "", "taller": c.canjeado_taller})
    # Las citas no tienen cuenta: se reconocen por el celular del motero.
    ultimos = moto_perfil.celular[-4:]  # prefiltro amplio; abajo se compara el número completo normalizado
    for s in SolicitudCita.objects.filter(telefono__contains=ultimos).select_related("taller", "servicio")[:limite]:
        try:
            if normalizar_celular(s.telefono) != moto_perfil.celular:
                continue
        except Exception:
            continue
        eventos.append({"fecha": s.creado.date(), "tipo": "cita", "moto": "",
                        "titulo": f"Cita: {s.servicio}" if s.servicio else "Cita en taller",
                        "detalle": f"{s.get_estado_display()} · para el {s.fecha_preferida:%d/%m/%Y}",
                        "lugar": str(s.taller), "url": s.taller.get_absolute_url(), "taller": s.taller})
    eventos.sort(key=lambda e: e["fecha"], reverse=True)
    return eventos[:limite]


def actividad_con_talleres(eventos, usuario=None):
    """Tu relación con los talleres: un resumen y un grupo por taller (lo que hiciste tú mismo queda en la bitácora de cada moto)."""
    grupos = {}
    for e in eventos:
        if not e.get("lugar"):
            continue  # "Lo hice yo"
        taller = e.get("taller")
        clave = taller.pk if taller else f"otro:{e['lugar'].lower()}"
        g = grupos.setdefault(clave, {"nombre": e["lugar"], "taller": taller, "url": e.get("url", ""), "eventos": [],
                                      "conteos": {"mantenimiento": 0, "cupon": 0, "cita": 0}})
        g["eventos"].append(e)
        g["conteos"][e["tipo"]] += 1
    lista = []
    for g in grupos.values():
        g["eventos"].sort(key=lambda e: e["fecha"], reverse=True)
        g["ultimo"] = g["eventos"][0]
        g["visitas"] = len(g["eventos"])
        g["tipos"] = " ".join(t for t, n in g["conteos"].items() if n)
        lista.append(g)
    lista.sort(key=lambda g: g["ultimo"]["fecha"], reverse=True)
    tipos = {e["tipo"] for g in lista for e in g["eventos"]}
    if usuario is not None:
        # La reseña que ya le dejaste a cada taller (para mostrarla y poder cambiarla).
        from talleres.models import Resena
        mias = {r.taller_id: r for r in Resena.objects.filter(usuario=usuario, taller__in=[g["taller"] for g in lista if g["taller"]])}
        for g in lista:
            g["mi_resena"] = mias.get(g["taller"].pk) if g["taller"] else None
    return {
        "talleres": lista,
        "resumen": {
            "talleres": len(lista),
            "mantenimientos": sum(g["conteos"]["mantenimiento"] for g in lista),
            "cupones": sum(g["conteos"]["cupon"] for g in lista),
            "citas": sum(g["conteos"]["cita"] for g in lista),
        },
        "filtros": [(t, n) for t, n in (("mantenimiento", "Mantenimientos"), ("cupon", "Cupones"), ("cita", "Citas")) if t in tipos],
    }


def filtros_del_historial(eventos):
    """Qué filtros tienen sentido según lo que hay en el historial (un filtro sin opciones no se muestra)."""
    tipos = {e["tipo"] for e in eventos}
    motos = sorted({e["moto"] for e in eventos if e.get("moto")})
    sistemas = sorted({e["sistema"] for e in eventos if e.get("sistema")})
    return {
        "tipos": [(t, n) for t, n in (("mantenimiento", "Mantenimientos"), ("cupon", "Cupones"), ("cita", "Citas")) if t in tipos],
        "lugar": "mantenimiento" in tipos,
        "motos": motos if len(motos) > 1 else [],
        "sistemas": sistemas if len(sistemas) > 1 else [],
    }


def motociclista_de(usuario):
    return getattr(usuario, "motociclista", None)


@login_required
def mi_cuenta(request):
    if roles.rol_de(request.user) == roles.SIN_PERFIL:
        return redirect("cuentas:completar")
    moto = motociclista_de(request.user)
    contexto = {"moto": moto}
    if moto:
        codigos = moto.codigos.select_related("cupon", "cupon__taller", "canjeado_taller")
        contexto.update({
            "disponibles": [c for c in codigos if not c.canjeado and c.cupon.vigente],
            "usados": [c for c in codigos if c.canjeado or not c.cupon.vigente][:50],
            "suscripcion": moto.suscripcion_activa,
            "solicitud": moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first(),
            "regalo": Cupon.regalo_actual(),
            "enlace_referido": request.build_absolute_uri(reverse("cupones:referido", args=[moto.codigo_referido])),
            "num_referidos": moto.referidos.count(),
            "servicios": (servicios := historial_servicios(moto)),
            "filtros_historial": filtros_del_historial(servicios),
            "actividad": actividad_con_talleres(servicios, request.user),
            "invitacion_whatsapp": "Encuentra talleres de motos de confianza en TallerYa y llévate un cupón: "
                                   + request.build_absolute_uri(reverse("cupones:referido", args=[moto.codigo_referido])),
            "motos": [(m, calcular_plan(m)) for m in moto.motos.select_related("linea", "linea__marca")],
        })
    if hasattr(request.user, "taller"):
        contexto["taller"] = request.user.taller
    contexto["preguntas"] = (request.user.preguntas.filter(visible=True)
                             .annotate(n_respuestas=Count("respuestas", filter=Q(respuestas__visible=True)))[:50])
    perfil = Perfil.de(request.user)
    contexto["perfil"] = perfil
    contexto["avatares"] = [(clave, datos[0], svg_predisenado(clave, 52)) for clave, datos in PREDISENADOS.items()]
    return render(request, "cuentas/mi_cuenta.html", contexto)


def plus(request):
    moto = motociclista_de(request.user) if request.user.is_authenticated else None
    solicitud = moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).first() if moto else None
    texto = "Hola TallerYa, quiero activar Plus."
    if moto:
        texto += f" Mi correo es {request.user.email}. Adjunto el comprobante de pago."
    return render(request, "cuentas/plus.html", {
        "moto": moto,
        "suscripcion": moto.suscripcion_activa if moto else None,
        "solicitud": solicitud,
        "precio": settings.PLUS_PRECIO_MENSUAL,
        "nequi": settings.PLUS_NEQUI,
        "dias": settings.PLUS_DIAS,
        "whatsapp_pago": f"https://wa.me/{settings.TALLERYA_WHATSAPP}?text={quote(texto)}",
        "exclusivos": Cupon.objects.disponibles().filter(solo_plus=True)[:3],
    })


@login_required
@require_POST
def solicitar_plus(request):
    moto = motociclista_de(request.user)
    if not moto:
        messages.error(request, "Tu cuenta no tiene un celular asociado. Escríbenos para ayudarte.")
        return redirect("cuentas:plus")
    if not moto.suscripciones.filter(estado=Suscripcion.Estado.SOLICITADA).exists():
        Suscripcion.objects.create(motociclista=moto)
    messages.success(request, "¡Solicitud recibida! Haz el pago y envíanos el comprobante por WhatsApp para activarte.")
    return redirect("cuentas:plus")


@login_required
@require_POST
def reclamar_regalo(request):
    moto = motociclista_de(request.user)
    if not moto:
        return redirect("cuentas:mi_cuenta")
    try:
        codigo, nuevo = reclamar_regalo_mensual(moto)
    except CuponNoDisponible as e:
        messages.error(request, str(e))
        return redirect("cuentas:mi_cuenta")
    if not nuevo:
        messages.info(request, "Ya reclamaste el regalo de este mes. Aquí está tu código.")
    return redirect(codigo)


# ---------------- Administración básica (solo staff) ----------------
@staff_member_required(login_url="cuentas:entrar")
def administracion(request):
    q = request.GET.get("q", "").strip()
    filtro = request.GET.get("rol", "")
    usuarios = User.objects.select_related("taller", "motociclista", "perfil").order_by("-date_joined")
    if q:
        usuarios = usuarios.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(taller__nombre__icontains=q))
    filas = [(u, r, roles.NOMBRES[r]) for u in usuarios[:200] for r in [roles.rol_de(u)]]
    if filtro in roles.NOMBRES:
        filas = [f for f in filas if f[1] == filtro]
    todos = [roles.rol_de(u) for u in User.objects.select_related("taller", "motociclista")]
    conteos = {r: todos.count(r) for r in (roles.MOTERO, roles.TALLER, roles.ADMIN)}
    return render(request, "cuentas/administracion.html", {
        "filas": filas, "q": q, "filtro": filtro, "conteos": conteos, "nombres": roles.NOMBRES,
        "pendientes": Taller.objects.filter(activo=False).select_related("barrio", "usuario").order_by("creado"),
    })


@staff_member_required(login_url="cuentas:entrar")
@require_POST
def aprobar_taller(request, pk):
    taller = get_object_or_404(Taller, pk=pk)
    taller.activo = True
    taller.save(update_fields=["activo"])
    if taller.usuario:
        from notificaciones.models import Notificacion
        from notificaciones.servicios import notificar
        notificar(taller.usuario, f"taller-aprobado:{taller.pk}", "¡Tu taller ya está publicado!",
                  f"{taller.nombre} aparece en el directorio de TallerYa.", taller.get_absolute_url(), Notificacion.Tipo.TALLER)
    messages.success(request, f"{taller} quedó publicado en el directorio.")
    return redirect("cuentas:administracion")



@login_required
@require_POST
def cambiar_avatar(request):
    perfil = Perfil.de(request.user)
    form = AvatarForm(request.POST, request.FILES)
    sin_recargar = request.headers.get("X-Requested-With") == "fetch"

    def fallo(texto):
        if sin_recargar:
            return JsonResponse({"ok": False, "error": texto}, status=400)
        messages.error(request, texto)
        return redirect(reverse("cuentas:mi_cuenta") + "#avatar")

    if not form.is_valid():
        errores = [e for lista in form.errors.values() for e in lista]
        return fallo(" ".join(errores) or "No pudimos cambiar tu avatar.")
    foto = form.cleaned_data.get("foto")
    eleccion = form.cleaned_data.get("eleccion", "")
    if foto:
        try:
            nueva = foto_cuadrada(foto)
        except Exception:
            return fallo("No pudimos leer esa imagen. Prueba con una foto JPG o PNG.")
        if perfil.avatar_foto:
            perfil.avatar_foto.delete(save=False)
        perfil.avatar_foto.save("avatar.jpg", nueva, save=False)
    elif eleccion != "foto" and perfil.avatar_foto:
        # Eligió la inicial o un prediseñado: la foto anterior se borra.
        perfil.avatar_foto.delete(save=False)
    if eleccion in PREDISENADOS:
        perfil.avatar_predisenado = eleccion
    elif eleccion == "":
        perfil.avatar_predisenado = ""
    perfil.save()
    if sin_recargar:
        # El navegador cambia el avatar en la página (encabezado y navbar) sin recargar.
        request.user.perfil = perfil
        return JsonResponse({
            "ok": True, "mensaje": "Avatar actualizado.",
            "grande": str(html_avatar(request.user, 64)), "chico": str(html_avatar(request.user, 28)),
            "foto": perfil.avatar_foto.url if perfil.avatar_foto else None,
        })
    messages.success(request, "Avatar actualizado.")
    return redirect("cuentas:mi_cuenta")  # sin #avatar: la ventana queda cerrada (solo se reabre si hubo un error)



# ---------------- Ingreso con Google ----------------
def _volver_google(request):
    return request.build_absolute_uri(reverse("cuentas:google_volver"))


def google_entrar(request):
    if not google.configurado():
        messages.error(request, "El ingreso con Google todavía no está disponible.")
        return redirect("cuentas:entrar")
    siguiente = request.GET.get("next", "")
    if url_has_allowed_host_and_scheme(siguiente, {request.get_host()}, require_https=request.is_secure()):
        request.session["google_siguiente"] = siguiente
    return redirect(google.url_autorizacion(_volver_google(request), request.session))


def google_volver(request):
    if not google.configurado():
        return redirect("cuentas:entrar")
    try:
        datos = google.datos_de_la_cuenta(request.GET, _volver_google(request), request.session)
    except google.ErrorGoogle as error:
        messages.error(request, str(error))
        return redirect("cuentas:entrar")

    perfil = Perfil.objects.select_related("usuario").filter(google_sub=datos["sub"]).first()
    usuario = perfil.usuario if perfil else User.objects.filter(username=datos["email"]).first()
    nueva = usuario is None
    if nueva:
        usuario = User.objects.create_user(username=datos["email"], email=datos["email"], first_name=datos["nombre"])
        usuario.set_unusable_password()  # entra con Google; puede crear una contraseña con "Olvidé mi contraseña"
        usuario.save()
    if not usuario.is_active:
        messages.error(request, "Esta cuenta está desactivada.")
        return redirect("cuentas:entrar")
    perfil = Perfil.de(usuario)
    if perfil.google_sub != datos["sub"]:
        perfil.google_sub = datos["sub"]
        perfil.save(update_fields=["google_sub"])
    login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")

    if roles.rol_de(usuario) == roles.SIN_PERFIL:
        messages.success(request, f"¡Hola, {usuario.first_name or 'bienvenido'}! Cuéntanos cómo vas a usar TallerYa.")
        return redirect("cuentas:completar")
    messages.success(request, f"¡Hola de nuevo, {usuario.first_name or usuario.email}!")
    return redirect(request.session.pop("google_siguiente", "") or "talleres:inicio")


@login_required
def completar_perfil(request):
    """Cuentas sin rol (p. ej. creadas con Google): eligen ser motero (celular) o registrar su taller."""
    if roles.rol_de(request.user) != roles.SIN_PERFIL:
        return redirect("cuentas:mi_cuenta")
    tipo = request.GET.get("tipo")
    if tipo == "motero":
        form = CelularForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            moto = form.motociclista_existente or Motociclista(celular=form.cleaned_data["celular"],
                                                                 nombre=request.user.first_name or "Motociclista")
            if not moto.pk and (ref := request.session.get("ref")):
                moto.referido_por = Motociclista.objects.filter(codigo_referido=ref).first()
            moto.usuario = request.user
            moto.save()
            messages.success(request, "¡Listo! Ya puedes agregar tu moto al garaje.")
            return redirect(request.session.pop("google_siguiente", "") or "talleres:inicio")
        return render(request, "cuentas/completar_motero.html", {"form": form})
    if tipo == "taller":
        negocio = RegistroTallerForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and negocio.is_valid():
            taller = negocio.save(commit=False)
            taller.usuario = request.user
            taller.activo = False
            taller.save()
            negocio.save_m2m()
            messages.success(request, "¡Recibimos tu taller! Lo revisaremos y lo publicaremos pronto.")
            return redirect("cuentas:mi_cuenta")
        return render(request, "cuentas/completar_taller.html", {"negocio": negocio})
    return render(request, "cuentas/registro_elegir.html", {"completar": True})



@login_required
@require_POST
def calificar_taller(request, pk):
    """Crea o actualiza la reseña de la cuenta para un taller (desde "Mi actividad con talleres")."""
    from talleres.models import Resena, Taller
    taller = get_object_or_404(Taller, pk=pk, activo=True)
    try:
        estrellas = int(request.POST.get("estrellas", ""))
    except ValueError:
        estrellas = 0
    comentario = request.POST.get("comentario", "").strip()[:600]
    if not 1 <= estrellas <= 5:
        messages.error(request, "Elige de 1 a 5 estrellas.")
        return redirect(reverse("cuentas:mi_cuenta") + "#actividad")
    nombre = (request.user.first_name or request.user.get_username().split("@")[0])[:80]
    resena, creada = Resena.objects.update_or_create(
        taller=taller, usuario=request.user,
        defaults={"estrellas": estrellas, "comentario": comentario or "Sin comentario.", "nombre": nombre})
    messages.success(request, f"¡Gracias! Calificaste a {taller.nombre} con {estrellas} estrella{'s' if estrellas > 1 else ''}."
                     if creada else f"Actualizamos tu reseña de {taller.nombre}.")
    return redirect(reverse("cuentas:mi_cuenta") + "#actividad")
