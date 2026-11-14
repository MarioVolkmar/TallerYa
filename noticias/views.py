from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .models import Articulo
from .servicios import refrescar_si_toca


def lista(request):
    refrescar_si_toca()
    articulos = Articulo.objects.filter(publicado=True)
    categoria = request.GET.get("categoria")
    if categoria in Articulo.Categoria.values:
        articulos = articulos.filter(categoria=categoria)
    pagina = Paginator(articulos, 12).get_page(request.GET.get("pagina"))
    return render(request, "noticias/lista.html", {
        "pagina": pagina, "categoria": categoria, "categorias": Articulo.Categoria.choices,
    })


def articulo(request, slug):
    a = get_object_or_404(Articulo, slug=slug, publicado=True)
    if a.externo:
        return redirect(a.fuente_url)
    otros = Articulo.objects.filter(publicado=True).exclude(pk=a.pk)[:3]
    return render(request, "noticias/articulo.html", {"a": a, "otros": otros})
