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
from .forms import PerfilMecanicoForm, ResenaMecanicoForm
from .models import MecanicoDomicilio, ResenaMecanico, TipoServicio, Zona

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


def listado(request):
    f = request.GET
    mecanicos = MecanicoDomicilio.objects.publicados().prefetch_related("zonas", "servicios")
    if q := f.get("q", "").strip()[:80]:
        mecanicos = mecanicos.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            | Q(pk__in=MecanicoDomicilio.servicios.through.objects.filter(tiposervicio__nombre__icontains=q).values("mecanicodomicilio_id"))
            | Q(pk__in=MecanicoDomicilio.marcas.through.objects.filter(marca__nombre__icontains=q).values("mecanicodomicilio_id")))
    zona = Zona.objects.filter(pk=f["zona"]).first() if f.get("zona", "").isdigit() else None
    servicio = TipoServicio.objects.filter(pk=f["servicio"]).first() if f.get("servicio", "").isdigit() else None
    if zona:
        mecanicos = mecanicos.filter(zonas=zona)
    if servicio:
        mecanicos = mecanicos.filter(servicios=servicio)
    if f.get("urgencias"):
        mecanicos = mecanicos.filter(urgencias=True)
    if f.get("verificados"):
        mecanicos = mecanicos.filter(verificado=True)
    mecanicos = _con_nota(mecanicos).order_by("-verificado", "-prom", "-n_resenas", "nombre", "pk")

    pagina = Paginator(mecanicos, POR_PAGINA).get_page(f.get("pagina"))
    for m in pagina:
        m.estrellas_pct = round(m.prom * 20)
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
    for clave, nombre in (("urgencias", "Atiende urgencias"), ("verificados", "Solo verificados")):
        if f.get(clave):
            activos.append({"nombre": nombre, "quitar": "?" + sin(clave)})

    publicados = MecanicoDomicilio.objects.publicados()
    return render(request, "domicilio/listado.html", {
        "pagina": pagina, "qs_pagina": sin(), "filtros": f, "filtros_activos": activos,
        "zonas": Zona.objects.all(), "servicios": TipoServicio.objects.all(),
        "stats": publicados.aggregate(total=Count("pk"), verificados=Count("pk", filter=Q(verificado=True)),
                                      urgencias=Count("pk", filter=Q(urgencias=True))),
        "mi_perfil": _perfil_de(request.user),
    })


def _perfil_de(usuario):
    if not usuario.is_authenticated:
        return None
    return MecanicoDomicilio.objects.filter(usuario=usuario).first()


def _clave_resena(request, mecanico):
    return f"resenas-mec:{mecanico.pk}:u{request.user.pk}", f"resenas-mec-dia:u{request.user.pk}"


def ficha(request, slug):
    mecanico = get_object_or_404(
        MecanicoDomicilio.objects.prefetch_related("zonas", "servicios", "marcas"), slug=slug)
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
    return render(request, "domicilio/ficha.html", {
        "m": mecanico, "es_dueno": es_dueno, "resenas": resenas, "nota": nota,
        "reparto": [(n, c, round(c * 100 / len(resenas)) if resenas else 0) for n, c in reparto.items()],
        "form": form, "mi_resena": mi_resena,
    })


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
        if nueva_cuenta:
            login(request, usuario, backend="cuentas.backends.Backend")
            Perfil.objects.update_or_create(usuario=usuario, defaults={"terminos_aceptados": timezone.now()})
            correos.enviar_verificacion(request, usuario)
        messages.success(request, "¡Listo! Revisaremos tu perfil y lo publicaremos pronto. Mientras tanto puedes verlo y editarlo aquí.")
        return redirect("domicilio:mi_perfil")
    return render(request, "domicilio/registro.html", {"cuenta": cuenta, "form": perfil, "nueva_cuenta": nueva_cuenta})


@login_required
def mi_perfil(request):
    mecanico = _perfil_de(request.user)
    if not mecanico:
        return redirect("domicilio:registro")
    form = PerfilMecanicoForm(request.POST or None, request.FILES or None, instance=mecanico)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Guardamos los cambios de tu perfil.")
        return redirect("domicilio:mi_perfil")
    return render(request, "domicilio/mi_perfil.html", {
        "m": mecanico, "form": form,
        "n_resenas": mecanico.resenas.filter(visible=True).count(),
    })

