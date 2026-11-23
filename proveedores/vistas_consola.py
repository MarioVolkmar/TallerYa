"""Páginas de la consola para proveedores: nuevo / editar (alta asistida), enlace de revisión listo para WhatsApp y
categorías. Dentro del marco de /consola/ (sección «Proveedores») y con bitácora de cada cambio."""
from urllib.parse import quote

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from consola import secciones
from consola.acciones import legible, registrar
from consola.permisos import es_superusuario, pagina_de_consola
from cuentas.limites import ip_cliente

from .consola import enlace_de
from .forms import CategoriaForm, ProveedorForm
from .models import Categoria, Proveedor
from .views import _campos_por_categoria

VOLVER = "?seccion=proveedores"


def _marco(request, plantilla, **contexto):
    filas, total = secciones.con_pendientes()
    filas = [(s, n) for s, n in filas if s.en_menu and (not s.superusuario or es_superusuario(request.user))]
    return render(request, "consola/consola.html", {
        "seccion": secciones.POR_CLAVE["proveedores"], "secciones": filas, "total_pendientes": total,
        "plantilla": plantilla, "pendientes_seccion": 0, **contexto})


def _cambios(form):
    """Detalle campo por campo para la bitácora (sin la foto: solo si cambió)."""
    salida = []
    for nombre in form.changed_data:
        if nombre == "autoriza":
            continue
        campo = form.fields[nombre]
        antes = form.initial.get(nombre)
        despues = form.cleaned_data.get(nombre)
        if nombre == "foto":
            antes, despues = "(foto anterior)" if antes else "", "(foto nueva)" if despues else ""
        salida.append({"campo": nombre, "etiqueta": str(campo.label or nombre), "antes": legible(antes)[:120],
                       "despues": legible(despues)[:120]})
    return salida


@pagina_de_consola
def editar(request, pk=None):
    """Sin pk: «Nuevo proveedor» (alta asistida: queda por revisar y se genera el enlace). Con pk: editar la ficha."""
    obj = get_object_or_404(Proveedor, pk=pk) if pk else None
    form = ProveedorForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        cambios = _cambios(form)
        nuevo = form.save(commit=False)
        if obj is None:
            nuevo.estado = Proveedor.Estado.POR_REVISAR
            nuevo.origen_alta = Proveedor.Alta.ASISTIDO
            nuevo.generar_token()
        nuevo.save()
        if obj is None:
            registrar(actor=request.user, clave="proveedores.alta_asistida",
                      frase=f"Dio de alta (asistida) al proveedor #{nuevo.pk} ({nuevo.nombre})", obj_tipo="proveedor",
                      obj_id=nuevo.pk, obj_repr=nuevo, cambios=[], ip=ip_cliente(request))
            messages.success(request, "Proveedor creado sin publicar. Envíale el enlace para que revise y apruebe.")
            return redirect("proveedores:enlace", pk=nuevo.pk)
        if cambios:
            registrar(actor=request.user, clave="proveedores.editar",
                      frase=f"Editó la ficha del proveedor #{nuevo.pk} ({nuevo.nombre})", obj_tipo="proveedor",
                      obj_id=nuevo.pk, obj_repr=nuevo, cambios=cambios, ip=ip_cliente(request))
            messages.success(request, f"Guardado: {nuevo.nombre}.")
        else:
            messages.info(request, "No había nada que cambiar.")
        return redirect(reverse("consola:inicio") + VOLVER)
    return _marco(request, "proveedores/consola_form.html", form=form, proveedor=obj,
                  campos_por_categoria=_campos_por_categoria())


@pagina_de_consola
def enlace(request, pk):
    """Enlace de revisión listo para copiar o mandar por WhatsApp (no cambia nada: renovar es una acción aparte)."""
    obj = get_object_or_404(Proveedor, pk=pk)
    url = enlace_de(request, obj) if obj.token_revision else ""
    texto = (f"Hola{' ' + obj.responsable.split()[0] if obj.responsable else ''}, te escribimos de TallerYa. "
             f"Cargamos la ficha de {obj.nombre} para mostrarla a los moteros de Medellín. Revísala, corrige lo que "
             f"haga falta y apruébala aquí (no necesitas cuenta): {url}")
    wa = f"https://wa.me/{obj.wa_numero}?text={quote(texto)}" if obj.wa_numero and url else ""
    return _marco(request, "proveedores/consola_enlace.html", proveedor=obj, url=url, wa=wa)


@pagina_de_consola
def categoria(request, pk=None):
    obj = get_object_or_404(Categoria, pk=pk) if pk else None
    form = CategoriaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        cambios = _cambios(form)
        cat = form.save()
        registrar(actor=request.user, clave="proveedores.categoria",
                  frase=f"{'Editó' if obj else 'Creó'} la categoría de proveedores «{cat.nombre}»", obj_tipo="categoria",
                  obj_id=cat.pk, obj_repr=cat, cambios=cambios, ip=ip_cliente(request))
        messages.success(request, f"Categoría «{cat.nombre}» guardada.")
        return redirect(reverse("consola:inicio") + VOLVER + f"&categoria={cat.slug}")
    return _marco(request, "proveedores/consola_categoria.html", form=form, categoria_obj=obj)
