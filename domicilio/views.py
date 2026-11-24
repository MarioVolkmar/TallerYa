"""Páginas de mecánicos a domicilio: listado público, ficha con reseñas, registro y edición del propio perfil.

Seguridad:
- El perfil propio se edita en /mecanicos/mi-perfil/ (sin id en la URL): solo se puede tocar el de la propia cuenta.
- Solo los APROBADOS salen al público; el dueño y el equipo ven la ficha aunque esté pendiente o suspendida.
- Registro con el mismo freno por IP que /cuenta/registro/; reseñas solo con cuenta y con límite por hora.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, FloatField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cuentas import correos, limites
from cuentas.forms import CuentaTallerForm
from cuentas.models import Perfil
from urllib.parse import quote

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from talleres import perfil as perfil_taller
from talleres import precios as perfil_precios

from talleres.models import Resena
from .identidad import estado_para_panel as estado_identidad
from .forms import PASO_OPCIONAL, PASO_TRABAJO, PASO_VERIFICACION, EdicionMecanicoForm, PerfilMecanicoForm, ResenaMecanicoForm, TallerDomicilioForm, foto_trabajo
from .models import FotoTrabajo, MecanicoDomicilio, MecanicoFavorito, ResenaMecanico, TallerDomicilio, TipoServicio, Zona

User = get_user_model()
POR_PAGINA = 12
REGISTRO_MAX_POR_HORA = 20          # igual que cuentas.views (envíos del formulario por IP)
RESENAS_MAX_POR_HORA = 3            # por cuenta y mecánico
RESENAS_MAX_POR_DIA_CUENTA = 10     # por cuenta, a todos los mecánicos


def _con_nota(qs):
    """Nota media y número de reseñas visibles calculados en la base de datos (ordena y pagina allí)."""
    resenas = ResenaMecanico.objects.filter(mecanico=OuterRef("pk"), visible=True).order_by().values("mecanico")
    return qs.annotate(
        prom=Coalesce(Subquery(resenas.annotate(p=Avg("estrellas")).values("p")), 0.0, output_field=FloatField()),
        n_resenas=Coalesce(Subquery(resenas.annotate(c=Count("pk")).values("c")), 0),
    )


def _talleres_con_domicilio(q, zona, servicio, urgencias, verificados):
    """Talleres aprobados que también van a domicilio, con los mismos filtros que los mecánicos (consultas fijas)."""
    qs = (TallerDomicilio.objects.publicados().select_related("taller", "taller__barrio")
          .prefetch_related("zonas", "servicios"))
    if q:
        qs = qs.filter(Q(taller__nombre__icontains=q) | Q(taller__descripcion__icontains=q)
                       | Q(pk__in=TallerDomicilio.servicios.through.objects.filter(tiposervicio__nombre__icontains=q).values("tallerdomicilio_id"))
                       | Q(taller__marcas__nombre__icontains=q)).distinct()
    if zona:
        qs = qs.filter(zonas=zona)
    if servicio:
        qs = qs.filter(servicios=servicio)
    if urgencias:
        qs = qs.filter(urgencias=True)
    if verificados:
        qs = qs.filter(taller__verificado=True)
    items = list(qs)
    notas = {r["taller"]: r for r in Resena.objects.filter(visible=True, taller__in=[d.taller_id for d in items])
             .values("taller").annotate(p=Avg("estrellas"), n=Count("id"))}
    for d in items:
        nota = notas.get(d.taller_id, {})
        d.es_taller, d.prom, d.n_resenas = True, nota.get("p") or 0.0, nota.get("n", 0)
        d.nombre, d.verificado = d.taller.nombre, d.taller.verificado
    return items


def listado(request):
    """Mecánicos independientes y talleres que también van a domicilio, en un solo listado con los mismos filtros."""
    f = request.GET
    tipo = f.get("tipo", "")
    q = f.get("q", "").strip()[:80]
    zona = Zona.objects.filter(pk=f["zona"]).first() if f.get("zona", "").isdigit() else None
    servicio = TipoServicio.objects.filter(pk=f["servicio"]).first() if f.get("servicio", "").isdigit() else None

    from cupones.models import Cupon
    con_cupon = Cupon.objects.disponibles().filter(Q(mecanico__isnull=False) | Q(taller__isnull=False))
    desc_mecanicos = set(con_cupon.values_list("mecanico", flat=True)) - {None}
    desc_talleres = set(con_cupon.values_list("taller", flat=True)) - {None}
    solo_descuento = bool(f.get("descuento"))

    mecanicos = []
    if tipo != "talleres":
        qs = MecanicoDomicilio.objects.publicados().prefetch_related("zonas", "servicios")
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
                | Q(pk__in=MecanicoDomicilio.servicios.through.objects.filter(tiposervicio__nombre__icontains=q).values("mecanicodomicilio_id"))
                | Q(pk__in=MecanicoDomicilio.marcas.through.objects.filter(marca__nombre__icontains=q).values("mecanicodomicilio_id")))
        if zona:
            qs = qs.filter(zonas=zona)
        if servicio:
            qs = qs.filter(servicios=servicio)
        if f.get("urgencias"):
            qs = qs.filter(urgencias=True)
        if f.get("verificados"):
            qs = qs.filter(verificado=True)
        if solo_descuento:
            qs = qs.filter(pk__in=desc_mecanicos)
        mecanicos = list(_con_nota(qs))
    talleres = ([] if tipo == "independientes" else
                _talleres_con_domicilio(q, zona, servicio, f.get("urgencias"), f.get("verificados")))
    if solo_descuento:
        talleres = [d for d in talleres if d.taller_id in desc_talleres]
    # Un solo orden para todos: verificados primero, luego nota y número de reseñas
    todos = sorted(mecanicos + talleres,
                   key=lambda x: (not x.verificado, -(x.prom or 0), -x.n_resenas, x.nombre.lower()))

    pagina = Paginator(todos, POR_PAGINA).get_page(f.get("pagina"))
    for m in pagina:
        m.estrellas_pct = round((m.prom or 0) * 20)
        m.tiene_descuento = (m.taller_id in desc_talleres) if getattr(m, "es_taller", False) else (m.pk in desc_mecanicos)
        servicios = list(m.servicios.all())
        m.servicios_vista, m.servicios_mas = servicios[:4], max(len(servicios) - 4, 0)
        zonas = list(m.zonas.all())
        m.zonas_vista, m.zonas_mas = zonas[:3], max(len(zonas) - 3, 0)

    def sin(*claves):
        resto = f.copy()
        for c in claves + ("pagina",):
            resto.pop(c, None)
        return resto.urlencode()

    activos = []
    if q:
        activos.append({"nombre": f"“{q}”", "quitar": "?" + sin("q")})
    if zona:
        activos.append({"nombre": str(zona), "quitar": "?" + sin("zona")})
    if servicio:
        activos.append({"nombre": str(servicio), "quitar": "?" + sin("servicio")})
    if tipo in ("independientes", "talleres"):
        activos.append({"nombre": "Solo independientes" if tipo == "independientes" else "Solo talleres",
                        "quitar": "?" + sin("tipo")})
    for clave, nombre in (("urgencias", "Atiende urgencias"), ("verificados", "Solo verificados"), ("descuento", "Con cupón")):
        if f.get(clave):
            activos.append({"nombre": nombre, "quitar": "?" + sin(clave)})

    stats = MecanicoDomicilio.objects.publicados().aggregate(
        total=Count("pk"), verificados=Count("pk", filter=Q(verificado=True)),
        urgencias=Count("pk", filter=Q(urgencias=True)))
    stats["talleres"] = TallerDomicilio.objects.publicados().count()
    return render(request, "domicilio/listado.html", {
        "pagina": pagina, "qs_pagina": sin(), "filtros": f, "filtros_activos": activos,
        "zonas": Zona.objects.all(), "servicios": TipoServicio.objects.all(), "stats": stats,
        "mi_perfil": _perfil_de(request.user),
        "mi_taller": getattr(request.user, "taller", None) if request.user.is_authenticated else None,
    })


def _perfil_de(usuario):
    if not usuario.is_authenticated:
        return None
    return MecanicoDomicilio.objects.filter(usuario=usuario).first()


def _clave_resena(request, mecanico):
    return f"resenas-mec:{mecanico.pk}:u{request.user.pk}", f"resenas-mec-dia:u{request.user.pk}"


def ficha(request, slug):
    mecanico = get_object_or_404(
        MecanicoDomicilio.objects.prefetch_related("zonas", "servicios", "marcas", "fotos_trabajo"), slug=slug)
    es_dueno = request.user.is_authenticated and mecanico.usuario_id == request.user.pk
    if not mecanico.publicado and not (es_dueno or request.user.is_staff):
        raise Http404("Este perfil no está publicado.")

    mi_resena = (ResenaMecanico.objects.filter(mecanico=mecanico, usuario=request.user).first()
                 if request.user.is_authenticated else None)
    form = ResenaMecanicoForm(instance=mi_resena)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        clave_hora, clave_dia = _clave_resena(request, mecanico)
        if not mecanico.publicado:
            messages.error(request, "Solo se pueden calificar perfiles publicados.")
            return redirect(mecanico)
        if es_dueno:
            messages.error(request, "No puedes calificar tu propio perfil.")
            return redirect(mecanico)
        if limites.superado(clave_hora, RESENAS_MAX_POR_HORA) or limites.superado(clave_dia, RESENAS_MAX_POR_DIA_CUENTA):
            messages.error(request, "Enviaste varias seguidas. Intenta de nuevo en un rato.")
            return redirect(mecanico)
        form = ResenaMecanicoForm(request.POST, instance=mi_resena)
        if form.is_valid():
            resena = form.save(commit=False)
            resena.mecanico, resena.usuario = mecanico, request.user
            resena.nombre = (request.user.first_name or request.user.get_username().split("@")[0])[:80]
            resena.save()
            limites.sumar(clave_hora, 3600)
            limites.sumar(clave_dia, 24 * 3600)
            messages.success(request, "Actualizamos tu reseña." if mi_resena else "¡Gracias por tu reseña!")
            return redirect(mecanico.get_absolute_url() + "#resenas")

    resenas = list(mecanico.resenas.filter(visible=True))
    reparto = {n: 0 for n in range(5, 0, -1)}
    for r in resenas:
        reparto[r.estrellas] += 1
    prom = sum(r.estrellas for r in resenas) / len(resenas) if resenas else None
    nota = {"prom": prom, "n": len(resenas), "pct": round(prom * 20) if prom else 0}

    # Mismas secciones que el detalle del taller, numeradas solo las que se muestran
    fotos = list(mecanico.fotos_trabajo.all())
    zonas = list(mecanico.zonas.all())
    especialidades = perfil_taller.especialidades_texto(mecanico.especialidades)
    compromisos = perfil_taller.compromisos_lista(mecanico)
    marcas = [] if mecanico.multimarca else list(mecanico.marcas.all())
    herramientas = mecanico.herramientas_lista
    verificaciones = _verificaciones(mecanico, fotos)
    from talleres.views import _tabla_precios  # misma tabla «Precios desde» del taller (PrecioMecanico tiene sus campos)
    # Como el taller: sin precios públicos la tabla no se manda y todos los servicios van como chips
    tabla_precios = _tabla_precios(mecanico) if mecanico.mostrar_precios else {"columnas": [], "filas": []}
    con_precio = {f["pk"] for f in tabla_precios["filas"]}
    from cupones.models import Cupon
    from .vista_descuentos import codigo_disponible
    descuentos = list(Cupon.objects.disponibles().filter(mecanico=mecanico)) if mecanico.publicado else []
    nombres = [n for n, hay in (("trabajo", especialidades or marcas or mecanico.multimarca or compromisos or herramientas or mecanico.anios_experiencia),
                                ("descuentos", descuentos), ("resenas", True), ("cobertura", True)) if hay]
    numeros = {n: f"{i:02d}" for i, n in enumerate(nombres, start=1)}
    medellin = [z for z in zonas if z.ciudad == "Medellín"]
    return render(request, "domicilio/ficha.html", {
        "m": mecanico, "es_dueno": es_dueno, "resenas": resenas, "nota": nota,
        "reparto": [(n, c, round(c * 100 / len(resenas)) if resenas else 0) for n, c in reparto.items()],
        "form": form, "mi_resena": mi_resena, "abrir_resena": request.method == "POST",
        "fotos": fotos, "zonas": zonas, "zonas_medellin": medellin,
        "zonas_municipios": [z for z in zonas if z.ciudad != "Medellín"],
        "especialidades": especialidades, "compromisos": compromisos, "marcas": marcas, "herramientas": herramientas,
        "verificaciones": verificaciones, "numeros": numeros,
        "servicios": list(mecanico.servicios.all()), "cuando": CUANDO, "tabla_precios": tabla_precios,
        "otros_servicios": [s for s in mecanico.servicios.all() if s.pk not in con_precio],
        "es_favorito": request.user.is_authenticated and MecanicoFavorito.objects.filter(
            usuario=request.user, mecanico=mecanico).exists(),
        "descuentos": descuentos, "mi_descuento": codigo_disponible(request.user, mecanico),
    })


def _verificaciones(mecanico, fotos):
    """Lo que el equipo sí verificó, en lenguaje simple, para el sello «Verificado por TallerYa» de la ficha.
    «verificado» lo marca el equipo después de revisar identidad y experiencia (ver el admin); cada línea sale solo
    si además hay con qué respaldarla. Sin «verificado» no hay sello (lista vacía)."""
    if not mecanico.verificado:
        return []
    lineas = []
    if mecanico.cedula_huella:
        lineas.append("Identidad confirmada")
    if mecanico.anios_experiencia or fotos:
        lineas.append("Experiencia revisada")
    if mecanico.referencias.strip():
        lineas.append("Referencias comprobadas")
    return lineas or ["Perfil revisado por el equipo"]


CUANDO = [("ahora", "Ahora mismo (estoy varado)"), ("hoy", "Hoy"), ("manana", "Mañana"), ("semana", "Esta semana")]


def visita(request, slug):
    """«Solicitar visita»: arma el mensaje de WhatsApp con lo que eligió el motociclista y lo lleva a wa.me.
    Por POST (con nombre y celular) además guarda la solicitud: el mecánico la ve en su bandeja, la cotiza y el
    motero la acepta desde su enlace (vista_solicitudes.py). Solo acepta servicios y zonas del mecánico."""
    mecanico = get_object_or_404(MecanicoDomicilio.objects.publicados(), slug=slug)
    g = request.POST if request.method == "POST" else request.GET
    servicio = mecanico.servicios.filter(pk=g["servicio"]).first() if g.get("servicio", "").isdigit() else None
    zona = mecanico.zonas.filter(pk=g["zona"]).first() if g.get("zona", "").isdigit() else None
    cuando = dict(CUANDO).get(g.get("cuando", ""), "")
    moto = " ".join(g.get("moto", "").split())[:60]
    detalle = " ".join(g.get("detalle", "").split())[:300]
    lineas = [f"Hola {mecanico.nombre}, te encontré en TallerYa y quiero pedir una visita a domicilio."]
    for etiqueta, valor in (("Servicio", servicio), ("Zona", zona), ("Moto", moto), ("Cuándo", cuando), ("Detalle", detalle)):
        if valor:
            lineas.append(f"{etiqueta}: {valor}")
    from .vista_descuentos import codigo_disponible
    descuento = codigo_disponible(request.user, mecanico)
    if request.method == "POST":
        from .vista_solicitudes import guardar_solicitud
        if solicitud := guardar_solicitud(request, mecanico, servicio, zona, g.get("cuando", ""), moto, detalle):
            descuento = solicitud.codigo_cupon
            lineas.append(f"Mi solicitud en TallerYa: {request.build_absolute_uri(solicitud.get_absolute_url())}")
    if descuento:
        lineas.append(f"Tengo tu cupón de TallerYa: {descuento.cupon.titulo} (código {descuento.codigo})")
    return redirect(f"https://wa.me/{mecanico.whatsapp}?text={quote(chr(10).join(lineas))}")


@require_POST
def favorito(request, slug):
    """Guarda o quita un mecánico de favoritos (como talleres.views.favorito: JSON al corazón o redirección)."""
    mecanico = get_object_or_404(MecanicoDomicilio.objects.publicados(), slug=slug)
    es_fetch = request.headers.get("X-Requested-With") == "fetch"
    if not request.user.is_authenticated:
        entrar = f"{reverse(settings.LOGIN_URL)}?next={mecanico.get_absolute_url()}"
        return JsonResponse({"entrar": entrar}, status=401) if es_fetch else redirect(entrar)
    fav, creado = MecanicoFavorito.objects.get_or_create(usuario=request.user, mecanico=mecanico)
    if not creado:
        fav.delete()
    if es_fetch:
        return JsonResponse({"favorito": creado})
    destino = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(destino, {request.get_host()}, require_https=request.is_secure()):
        destino = mecanico.get_absolute_url()
    return redirect(destino)


def registro(request):
    """Crear el perfil de mecánico a domicilio. Sin sesión, crea también la cuenta (correo y contraseña).
    El perfil queda PENDIENTE hasta que un administrador lo apruebe (admin de Django o /consola/)."""
    if request.user.is_authenticated:
        if _perfil_de(request.user):
            return redirect("domicilio:mi_perfil")
        if getattr(request.user, "taller", None):
            messages.info(request, "Tu cuenta es de un taller. Para registrarte como mecánico a domicilio usa otra cuenta.")
            return redirect("talleres:panel")
    if request.method == "POST":  # mismo freno que /cuenta/registro/: enumeración de correos y spam de perfiles
        clave = f"registro:ip:{limites.ip_cliente(request)}"
        if limites.superado(clave, REGISTRO_MAX_POR_HORA):
            messages.error(request, "Demasiados intentos de registro desde tu conexión. Espera una hora e inténtalo de nuevo.")
            return redirect("domicilio:registro")
        limites.sumar(clave, 3600)

    nueva_cuenta = not request.user.is_authenticated
    cuenta = CuentaTallerForm(request.POST or None, prefix="cuenta") if nueva_cuenta else None
    perfil = PerfilMecanicoForm(request.POST or None, request.FILES or None,
                                initial={"nombre": request.user.first_name} if not nueva_cuenta else None)
    trabajos = request.FILES.getlist("trabajos")[:FotoTrabajo.MAXIMO] if request.method == "POST" else []
    if request.method == "POST" and perfil.is_valid() and (cuenta is None or cuenta.is_valid()):
        with transaction.atomic():
            usuario = request.user
            if nueva_cuenta:
                d = cuenta.cleaned_data
                usuario = User.objects.create_user(username=d["email"], email=d["email"], password=d["password1"],
                                                   first_name=perfil.cleaned_data["nombre"][:150])
            mecanico = perfil.save(commit=False)
            mecanico.usuario = usuario
            mecanico.estado = MecanicoDomicilio.Estado.PENDIENTE
            mecanico.verificado = False
            mecanico.save()
            perfil.save_m2m()
            rechazadas = _guardar_trabajos(mecanico, trabajos)
        from notificaciones.servicios import avisar_admins
        avisar_admins(f"registro-mecanico:{mecanico.pk}", "Mecánico nuevo por revisar", mecanico.nombre)
        if nueva_cuenta:
            login(request, usuario, backend="cuentas.backends.Backend")
            Perfil.objects.update_or_create(usuario=usuario, defaults={"terminos_aceptados": timezone.now()})
            correos.enviar_verificacion(request, usuario)
        if rechazadas:
            messages.error(request, f"{rechazadas} foto(s) de trabajos no se subieron: usa JPG, PNG o WEBP de máximo 5 MB.")
        messages.success(request, "¡Listo! Tu perfil quedó en revisión. Aquí ves su estado y lo que te falta.")
        return redirect("domicilio:mi_perfil")
    pasos = ([("cuenta", "Tu cuenta", list(cuenta))] if nueva_cuenta else []) + [
        ("trabajo", "Tu trabajo", perfil.campos(PASO_TRABAJO)),
        ("verificacion", "Verificación", perfil.campos(PASO_VERIFICACION)),
        ("opcional", "Completa tu perfil", perfil.campos(PASO_OPCIONAL)),
    ]
    grupos_zonas = _grupos_zonas(perfil)
    # El bloque plegado se abre si al reenviar trae algo escrito o con error (para no esconder lo que llenó)
    abrir_opcional = perfil.is_bound and any(perfil[n].errors or perfil[n].value() for n in PASO_OPCIONAL)
    return render(request, "domicilio/registro.html", {
        "cuenta": cuenta, "form": perfil, "nueva_cuenta": nueva_cuenta, "pasos": pasos,
        "grupos_zonas": grupos_zonas, "abrir_opcional": abrir_opcional, "maximo_trabajos": FotoTrabajo.MAXIMO})


def _grupos_zonas(form):
    """Chips de zonas agrupados (domicilio/_zonas_servicios.html): comunas de Medellín y municipios del Valle de Aburrá."""
    zonas = list(form["zonas"])
    medellin = [cb for cb in zonas if cb.data["value"].instance.ciudad == "Medellín"]
    return [("Medellín", True, medellin), ("Valle de Aburrá", False, [cb for cb in zonas if cb not in medellin])]


def _guardar_trabajos(mecanico, archivos):
    """Guarda hasta FotoTrabajo.MAXIMO fotos de trabajos (re-codificadas). Devuelve cuántas se rechazaron."""
    libres = FotoTrabajo.MAXIMO - mecanico.fotos_trabajo.count()
    rechazadas = 0
    for archivo in archivos[:max(libres, 0)]:
        limpia = foto_trabajo(archivo)
        if limpia:
            FotoTrabajo.objects.create(mecanico=mecanico, imagen=limpia)
        else:
            rechazadas += 1
    return rechazadas


@login_required
def panel(request):
    """«Mi panel» del mecánico a domicilio: acción principal, por hacer, accesos, precios y cifras del mes."""
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    from datetime import timedelta
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    solicitudes = mecanico.solicitudes
    resenas = mecanico.resenas.filter(visible=True)
    pasos = mecanico.pasos()
    hechos = sum(h for _, h, _ in pasos)
    from talleres.panel_cifras import faltan_cortos, franja, mes_anterior
    ini_ant, fin_ant = mes_anterior(hoy)
    n_mes = solicitudes.filter(creado__date__gte=inicio_mes).count()
    n_atendidas = solicitudes.filter(estado="atendida", creado__date__gte=inicio_mes).count()
    nota = resenas.aggregate(prom=Avg("estrellas"), n=Count("id"))
    url_sol = reverse("domicilio:solicitudes") + "?ver=todas"
    return render(request, "domicilio/panel.html", {
        "m": mecanico,
        "identidad_estado": estado_identidad(mecanico),
        "n_descuentos_vencidos": mecanico.cupones.filter(activo=True).exclude(pk__in=mecanico.cupones.vigentes()).count(),
        "franja": franja([
            ("Solicitudes del mes", n_mes, solicitudes.filter(creado__date__range=(ini_ant, fin_ant)).count(), "mes pasado",
             "", url_sol, "lava", "Comparte tu ficha para recibir solicitudes de visita."),
            ("Visitas atendidas", n_atendidas, solicitudes.filter(estado="atendida", creado__date__range=(ini_ant, fin_ant)).count(),
             "mes pasado", "", url_sol, "verde", "Cierra tus visitas para que cuenten aquí."),
            ("Calificación", f"{nota['prom']:.1f}".replace(".", ",") if nota["n"] else "", None, "",
             f"{nota['n']} reseña{'s' if nota['n'] != 1 else ''}", reverse("domicilio:resenas"), "mostaza",
             "Pídeles a tus clientes que te califiquen en tu ficha."),
            ("Te guardaron", mecanico.favoritos.count(), None, "", "moteros", "", "rosa", ""),
        ]),
        "precios_ocultos": bool(mecanico.precios.exists() and not mecanico.mostrar_precios),
        "n_por_cotizar": solicitudes.filter(estado="pendiente").count(),
        "n_por_cerrar": solicitudes.filter(estado="confirmada", fecha_propuesta__lte=hoy).count(),
        "n_abiertas": solicitudes.filter(estado__in=["pendiente", "cotizada", "confirmada"]).count(),
        "sin_responder": resenas.filter(respuesta="").count(),
        "nota": resenas.aggregate(prom=Avg("estrellas"), n=Count("id")),
        "pct": round(100 * hechos / len(pasos)),
        "faltan": [t for t, hecho, _ in pasos if not hecho][:3],
        "faltan_cortos": faltan_cortos([t for t, hecho, _ in pasos if not hecho]),
        "faltan_obligatorios": [t for t, hecho, obligatorio in pasos if obligatorio and not hecho],
        "n_precios": mecanico.precios.count(),
        "precios_por_confirmar": perfil_precios.necesita_confirmar(mecanico),
        "descuentos_activos": mecanico.cupones.vigentes().count(),
        "canjes_mes": mecanico.canjes.filter(canjeado_en__date__gte=inicio_mes).count(),
        "mes": {
            "solicitudes": solicitudes.filter(creado__date__gte=inicio_mes).count(),
            "atendidas": solicitudes.filter(estado="atendida", creado__date__gte=inicio_mes).count(),
            "resenas": resenas.filter(creado__date__gte=inicio_mes).count(),
        },
        "favoritos": mecanico.favoritos.count(),
        "recientes": list(solicitudes.filter(estado__in=["pendiente", "cotizada", "confirmada"])
                          .select_related("servicio", "zona")[:4]),
        "resenas_recientes": list(resenas[:3]),
        "tiene_garaje": hasattr(request.user, "motociclista"),
    })


@login_required
@require_POST
def alternar_precios(request):
    """Interruptor del panel: mostrar u ocultar los precios en la ficha pública. Solo el propio perfil."""
    mecanico = _perfil_de(request.user)
    if not mecanico:
        raise Http404
    mecanico.mostrar_precios = request.POST.get("valor") == "1"
    mecanico.save(update_fields=["mostrar_precios"])
    if request.headers.get("x-requested-with") == "fetch":  # interruptor sin recargar: sin mensaje ni redirección
        from django.http import HttpResponse
        return HttpResponse(status=204)
    messages.success(request, "Tus precios ahora se ven en tu ficha." if mecanico.mostrar_precios
                     else "Ocultamos tus precios: tu ficha dice «Cotiza por WhatsApp».")
    return redirect("domicilio:panel")


@login_required
@require_POST
def alternar_urgencias(request):
    """Interruptor del panel: salir o no a atender motos varadas. Solo el propio perfil."""
    mecanico = _perfil_de(request.user)
    if not mecanico:
        raise Http404
    mecanico.urgencias = request.POST.get("valor") == "1"
    mecanico.save(update_fields=["urgencias"])
    messages.success(request, "Ahora atiendes urgencias." if mecanico.urgencias else "Dejaste de atender urgencias.")
    return redirect("domicilio:panel")


@login_required
def mi_perfil(request):
    """El mecánico ve el estado de su perfil (pendiente, publicado, suspendido), lo que le falta, y lo edita."""
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    form = EdicionMecanicoForm(request.POST or None, request.FILES or None, instance=mecanico)
    if request.method == "POST" and form.is_valid():
        form.save()
        if rechazadas := _guardar_trabajos(mecanico, request.FILES.getlist("trabajos")):
            messages.error(request, f"{rechazadas} foto(s) de trabajos no se subieron: usa JPG, PNG o WEBP de máximo 5 MB.")
        if mecanico.estado == MecanicoDomicilio.Estado.RECHAZADO:  # corrigió: vuelve a la fila de revisión
            mecanico.estado, mecanico.motivo_rechazo = MecanicoDomicilio.Estado.PENDIENTE, ""
            mecanico.save(update_fields=["estado", "motivo_rechazo", "actualizado"])
            messages.success(request, "Guardamos los cambios y enviamos tu perfil a revisión otra vez.")
        else:
            messages.success(request, "Guardamos los cambios de tu perfil.")
        return redirect("domicilio:mi_perfil")
    pasos = mecanico.pasos()
    return render(request, "domicilio/mi_perfil.html", {
        "m": mecanico, "form": form, "pasos": pasos,
        "faltan_obligatorios": [t for t, hecho, obligatorio in pasos if obligatorio and not hecho],
        "faltan": [t for t, hecho, _ in pasos if not hecho][:3], "grupos_zonas": _grupos_zonas(form),
        "url_alternar": reverse("domicilio:alternar_precios"), "url_precios": reverse("domicilio:mis_precios"),
        "hechos": sum(h for _, h, _ in pasos), "total_pasos": len(pasos),
        "n_resenas": mecanico.resenas.filter(visible=True).count(),
        "fotos": mecanico.fotos_trabajo.all(), "maximo_trabajos": FotoTrabajo.MAXIMO,
        "resenas": mecanico.resenas.filter(visible=True), "n_precios": mecanico.precios.count(),
        "n_solicitudes": mecanico.solicitudes.filter(estado__in=["pendiente", "cotizada", "confirmada"]).count(),
    })


@login_required
def mis_precios(request):
    """El mecánico publica rangos «desde–hasta» por servicio y cilindraje (como «Mis precios» del taller)."""
    from .forms import precios_formset
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    Formset = precios_formset(mecanico)
    formset = Formset(request.POST or None, instance=mecanico, queryset=mecanico.precios.select_related("servicio"))
    from talleres import precios as _precios
    if request.method == "POST" and request.POST.get("siguen_vigentes"):
        _precios.confirmar_vigentes(mecanico)
        messages.success(request, "Listo: confirmaste que tus precios siguen vigentes.")
        return redirect("domicilio:mis_precios")
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Guardamos tus precios de referencia." if mecanico.mostrar_precios
                         else "Guardamos tus precios; tu ficha dice «Cotiza por WhatsApp» hasta que decidas mostrarlos.")
        return redirect("domicilio:mis_precios")
    from talleres.precios import agrupar_formset
    return render(request, "domicilio/mis_precios.html", {
        "m": mecanico, "formset": formset, "grupos": agrupar_formset(formset), "medianas": "{}",
        "servicios": formset.empty_form.fields["servicio"].queryset,
        "url_alternar": reverse("domicilio:alternar_precios"),
        "confirmado": _precios.fecha_confirmacion(mecanico), "por_confirmar": _precios.necesita_confirmar(mecanico),
        "sin_servicios": not mecanico.servicios.exists()})


@login_required
@require_POST
def responder_resena(request, pk):
    """El mecánico responde una reseña de su perfil (como el taller). Solo las de su propio perfil: 404 si no."""
    resena = get_object_or_404(ResenaMecanico, pk=pk, mecanico__usuario=request.user)
    texto = request.POST.get("respuesta", "").strip()[:600]
    resena.respuesta = texto
    resena.respondida_en = timezone.now() if texto else None
    resena.save(update_fields=["respuesta", "respondida_en"])
    messages.success(request, "Respuesta publicada en tu perfil." if texto else "Quitamos tu respuesta.")
    volver = request.POST.get("volver", "")
    if not url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        volver = reverse("domicilio:panel") + "#resenas"
    return redirect(volver)


@login_required
def resenas(request):
    """Todas las reseñas del mecánico, con filtro «sin responder» (como «Mis reseñas» del taller)."""
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    todas = mecanico.resenas.filter(visible=True)
    sin_responder = todas.filter(respuesta="").count()
    filtro = request.GET.get("ver", "todas")
    lista = todas.filter(respuesta="") if filtro == "sin_responder" else todas
    estrellas = request.GET.get("estrellas", "")
    if estrellas in {"1", "2", "3", "4", "5"}:
        lista = lista.filter(estrellas=int(estrellas))
    por_estrella = {r["estrellas"]: r["n"] for r in todas.values("estrellas").annotate(n=Count("id"))}
    nota = todas.aggregate(prom=Avg("estrellas"), n=Count("id"))
    nota["pct"] = round((nota["prom"] or 0) * 20)
    return render(request, "domicilio/resenas.html", {
        "m": mecanico, "nota": nota, "sin_responder": sin_responder, "filtro": filtro, "estrellas": estrellas,
        "reparto": [(e, por_estrella.get(e, 0), round(por_estrella.get(e, 0) * 100 / nota["n"]) if nota["n"] else 0)
                    for e in (5, 4, 3, 2, 1)],
        "lista": lista.order_by("-creado")})


@login_required
@require_POST
def borrar_trabajo(request, pk):
    """Borra una foto de trabajo. Se busca dentro de las fotos del propio perfil: otra cuenta recibe 404 (sin IDOR)."""
    foto = get_object_or_404(FotoTrabajo, pk=pk, mecanico__usuario=request.user)
    foto.imagen.delete(save=False)
    foto.delete()
    messages.success(request, "Borramos la foto.")
    return redirect("domicilio:mi_perfil")


@login_required
@require_POST
def alternar_taller(request):
    """Interruptor del panel del taller: prende o apaga «Servicio a domicilio» sin salir del panel. Solo su propio taller."""
    taller = getattr(request.user, "taller", None)
    if not taller:
        raise Http404
    servicio, _ = TallerDomicilio.objects.get_or_create(taller=taller)
    servicio.activo = request.POST.get("valor") == "1"
    servicio.save(update_fields=["activo", "actualizado"])
    if not servicio.activo:
        messages.success(request, "Apagado: ya no ofreces servicio a domicilio.")
    elif not servicio.zonas.exists():
        messages.success(request, "¡Listo! Ya ofreces servicio a domicilio. Elige las zonas que cubres para que te encuentren.")
        return redirect("domicilio:mi_taller")
    else:
        messages.success(request, "¡Listo! Ya ofreces servicio a domicilio en el directorio y en Mecánicos a domicilio.")
    return redirect("talleres:panel")


@login_required
def mi_taller(request):
    """El taller activa «También atiendo a domicilio». Solo el taller de la propia cuenta (sin id en la URL)."""
    taller = getattr(request.user, "taller", None)
    if not taller:
        messages.info(request, "Esta sección es para cuentas de taller.")
        return redirect("cuentas:mi_cuenta")
    servicio, _ = TallerDomicilio.objects.get_or_create(taller=taller)
    form = TallerDomicilioForm(request.POST or None, instance=servicio)
    if request.method == "POST" and form.is_valid():
        form.save()
        if not servicio.activo:
            texto = "Guardado. No sales en Mecánicos a domicilio mientras esté apagado."
        elif taller.activo:
            texto = "¡Listo! Ya sales en Mecánicos a domicilio."
        else:
            texto = "Guardado. Saldrás en Mecánicos a domicilio cuando aprobemos tu taller."
        messages.success(request, texto)
        return redirect("domicilio:mi_taller")
    return render(request, "domicilio/mi_taller.html", {"taller": taller, "form": form, "servicio": servicio,
                                                        "grupos_zonas": _grupos_zonas(form)})
