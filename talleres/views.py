from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from cupones.models import Cupon

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.views.decorators.http import require_POST

from .forms import PerfilTallerForm, RegistroTallerForm, ResenaForm, SolicitudCitaForm
from .models import Barrio, FotoTaller, Marca, Servicio, Taller


def inicio(request):
    talleres = Taller.objects.filter(activo=True).select_related("barrio").prefetch_related("servicios")
    f = request.GET
    if q := f.get("q", "").strip():
        talleres = talleres.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if f.get("barrio", "").isdigit():
        talleres = talleres.filter(barrio_id=f["barrio"])
    if f.get("servicio", "").isdigit():
        talleres = talleres.filter(servicios__id=f["servicio"])
    if f.get("marca", "").isdigit():
        talleres = talleres.filter(marcas__id=f["marca"])
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    return render(request, "talleres/inicio.html", {
        "motero": motero,
        "motos_portada": list(motero.motos.select_related("linea", "linea__marca")) if motero else [],
        "talleres": talleres.distinct(),
        "barrios": Barrio.objects.all(),
        "servicios": Servicio.objects.all(),
        "marcas": Marca.objects.all(),
        "filtros": f,
    })


def detalle(request, slug):
    taller = get_object_or_404(Taller.objects.select_related("barrio"), slug=slug, activo=True)
    motero = getattr(request.user, "motociclista", None) if request.user.is_authenticated else None
    inicial_cita = {}
    mis_motos = [m.nombre_completo for m in motero.motos.select_related("linea", "linea__marca")] if motero else []
    if motero:
        primera = motero.motos.select_related("linea", "linea__marca").first()
        inicial_cita = {"nombre": motero.nombre, "telefono": motero.celular,
                        "moto": primera.nombre_completo if primera else ""}
    if request.GET.get("servicio", "").isdigit():
        inicial_cita["servicio"] = request.GET["servicio"]
    cita_form = SolicitudCitaForm(taller=taller, initial=inicial_cita)
    resena_form = ResenaForm(initial={"nombre": request.user.first_name} if request.user.is_authenticated else None)
    abrir = ""

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cita":
            cita_form = SolicitudCitaForm(request.POST, taller=taller)
            form, msg, abrir = cita_form, "¡Solicitud enviada! El taller te contactará pronto.", "cita"
        else:
            resena_form = ResenaForm(request.POST)
            form, msg, abrir = resena_form, "¡Gracias por tu reseña!", "resena"
        if form.is_valid():
            obj = form.save(commit=False)
            obj.taller = taller
            if accion != "cita" and request.user.is_authenticated:
                obj.usuario = request.user
            obj.save()
            messages.success(request, msg)
            return redirect(taller)

    resenas = list(taller.resenas.filter(visible=True))
    reparto = {n: 0 for n in range(5, 0, -1)}
    for r in resenas:
        reparto[r.estrellas] += 1
    fotos = list(taller.fotos.all())
    cupones = Cupon.objects.disponibles().filter(Q(taller=taller) | Q(taller__isnull=True))
    # Numeración de las secciones según las que existan, para que siempre sea 01, 02, 03…
    nombres = ["sobre", "servicios"] + (["fotos"] if fotos else []) + (["cupones"] if cupones else []) + ["resenas"]
    numeros = {n: f"{i:02d}" for i, n in enumerate(nombres, start=1)}
    return render(request, "talleres/detalle.html", {
        "taller": taller,
        "resenas": resenas,
        "reparto": [(n, c, round(c * 100 / len(resenas)) if resenas else 0) for n, c in reparto.items()],
        "fotos": fotos,
        "cupones": cupones,
        "numeros": numeros,
        "cita_form": cita_form,
        "resena_form": resena_form,
        "abrir": abrir,
        "mis_motos": mis_motos,
        "es_mio": request.user.is_authenticated and getattr(request.user, "taller", None) == taller,
    })


@login_required
def editar_perfil(request):
    """El taller arma su perfil: descripción, horario, servicios, marcas, portada y galería."""
    taller = getattr(request.user, "taller", None)
    if not taller:
        messages.info(request, "Esta sección es para cuentas de taller.")
        return redirect("cuentas:mi_cuenta")
    form = PerfilTallerForm(request.POST or None, request.FILES or None, instance=taller)
    if request.method == "POST":
        nuevas = request.FILES.getlist("galeria")
        libres = FotoTaller.MAXIMO - taller.fotos.count()
        errores_fotos = []
        if len(nuevas) > libres:
            errores_fotos.append(f"Puedes tener máximo {FotoTaller.MAXIMO} fotos; te quedan {max(libres, 0)}.")
        for f in nuevas:
            if f.size > 5 * 1024 * 1024 or (f.content_type or "") not in ("image/jpeg", "image/png", "image/webp"):
                errores_fotos.append(f"«{f.name}» no se subió: usa JPG, PNG o WEBP de máximo 5 MB.")
        if form.is_valid() and not errores_fotos:
            form.save()
            for i, f in enumerate(nuevas):
                FotoTaller.objects.create(taller=taller, imagen=f, orden=taller.fotos.count() + i)
            messages.success(request, "¡Perfil actualizado!")
            return redirect("talleres:editar_perfil")
        for e in errores_fotos:
            messages.error(request, e)
    return render(request, "talleres/editar_perfil.html", {
        "form": form, "taller": taller, "fotos": taller.fotos.all(), "maximo": FotoTaller.MAXIMO,
    })


@login_required
@require_POST
def eliminar_foto(request, pk):
    foto = get_object_or_404(FotoTaller, pk=pk, taller__usuario=request.user)
    foto.imagen.delete(save=False)
    foto.delete()
    messages.success(request, "Foto eliminada.")
    return redirect("talleres:editar_perfil")


def registro(request):
    # Los talleres ahora se registran con cuenta propia (rol "taller").
    return redirect(reverse("cuentas:registro") + "?tipo=taller")



# ---------------- Páginas legales ----------------
PAGINAS_LEGALES = {
    "terminos": "Términos y condiciones",
    "privacidad": "Política de tratamiento de datos personales",
    "cupones": "Condiciones de los cupones",
    "cookies": "Política de cookies",
}


def legal(request, pagina):
    from django.conf import settings
    from django.http import Http404

    if pagina not in PAGINAS_LEGALES:
        raise Http404
    return render(request, f"legal/{pagina}.html", {
        "pagina": pagina, "titulo_legal": PAGINAS_LEGALES[pagina], "paginas_legales": PAGINAS_LEGALES,
        "legal": settings.LEGAL,
    })
