"""Paginación común de los listados de la consola: ?pagina= y ?por= (tamaño elegido entre OPCIONES_POR_PAGINA)."""
from django.core.paginator import Paginator

from .limites import OPCIONES_POR_PAGINA, POR_PAGINA


def paginar(request, qs, clave):
    por = request.GET.get("por", "")
    por = int(por) if por.isdigit() and int(por) in OPCIONES_POR_PAGINA else POR_PAGINA[clave]
    paginador = Paginator(qs, por)
    pagina = paginador.get_page(request.GET.get("pagina"))
    sin_pagina = request.GET.copy()
    sin_pagina.pop("pagina", None)
    sin_por = sin_pagina.copy()
    sin_por.pop("por", None)
    return {
        "pagina": pagina, "total": paginador.count, "por": por, "opciones_por": OPCIONES_POR_PAGINA,
        "rango_paginas": list(paginador.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1)),
        "elipsis": Paginator.ELLIPSIS, "query_sin_pagina": sin_pagina.urlencode(),
        "campos_sin_por": [(k, v) for k in sin_por for v in sin_por.getlist(k)],
    }
