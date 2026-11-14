"""Lectores de catálogos de despiece para el importador (formatos además de yamaha y auteco).

Cada lector recibe el documento (PyMuPDF) o, en "fichas", la carpeta, y devuelve
{clave_figura: {"titulo", "numero", "filas", "imagen"}}, donde "imagen" es una función que
renderiza el dibujo solo cuando hace falta (así no se procesan las láminas que el mapa no usa).

- honda: catálogos Honda por bloques ("E-2", "F-11-3"). El texto viene con una fuente desplazada
  (letras en U+F020-U+F0FF): se resta 0xF000. Bloque E-n se guarda como figura 100+n y F-n como 200+n.
- hero: catálogos Hero, por bloques como Honda pero con texto normal y el dibujo en la misma página.
- suzuki: catálogos Suzuki "FIG.103A (1-B-2) TÍTULO" o "Fig. 1 / TÍTULO".
- fichas: carpeta con fichas.json (secciones con imagen PNG y partes), bajadas de tiendas en línea.
"""
import json
import re
from pathlib import Path

RE_CODIGO = re.compile(r"\d{5}-[A-Z0-9]{2,5}-[A-Z0-9]{3,4}")
RE_PUNTOS = re.compile(r"\s*([·•]{2,}|\.{3,}|[·•.]\s+[\d(-]).*$")
# Columnas de modelo ("2TU", "7ID,8ID") o de color ("NH364M*SHEEN SILVER") que quedan en la línea de la descripción:
# la fila es otra versión de la pieza anterior con la misma referencia
RE_SOLO_MODELO = re.compile(r"^[0-9A-Z]{2,4}(\s*,\s*[0-9A-Z]{2,4})*$")
RE_COLOR = re.compile(r"^(?:[A-Z]\s*\*)?[A-Z]{1,2}\d{3}[A-Z]?\*")


def _decodificar(texto):
    return "".join(chr(ord(c) - 0xF000) if 0xF020 <= ord(c) <= 0xF0FF else c for c in texto)


def _numero_bloque(clave):
    m = re.match(r"([EF])-(\d+)", clave)
    return (100 if m.group(1) == "E" else 200) + int(m.group(2))


def _cantidad(texto):
    m = re.search(r"\b(\d{1,2})\b", texto)
    return int(m.group(1)) if m else 1


def _filas(lineas):
    """Filas de la tabla por líneas: la línea con el código trae (o va precedida de) la referencia;
    la siguiente es la descripción y la cantidad va al final de esa línea o en la línea siguiente."""
    filas, ref = [], None
    for i, linea in enumerate(lineas):
        m = RE_CODIGO.search(linea)
        if not m or i + 1 >= len(lineas):
            continue
        antes = linea[:m.start()].replace(" ", "")
        if re.fullmatch(r"\d{1,3}(-\d{1,2})?", antes):
            ref = int(antes.split("-")[0])
        elif i > 0 and re.fullmatch(r"\d{1,3}(-\d{1,2})?", lineas[i - 1].strip()):
            ref = int(lineas[i - 1].strip().split("-")[0])
        if ref is None:
            continue
        cruda = lineas[i + 1].strip().lstrip("*").strip()
        en_linea = linea[m.end():].strip()
        cantidad_en_linea = None
        if re.search(r"[A-Za-z]{2}", en_linea):           # la descripción (y la cantidad) vienen en la misma línea del código
            fin = re.search(r"\s{2,}(\d{1,2})\s*$", en_linea)
            if fin:
                cantidad_en_linea, en_linea = int(fin.group(1)), en_linea[:fin.start()]
            cruda = en_linea.strip()
        if RE_CODIGO.search(cruda):
            continue
        descripcion = RE_PUNTOS.sub("", cruda).strip(" ,")
        # Letra de la columna de variante pegada al inicio ("A SWINGARM SUB ASSY."); "O RING", "C RING", "E RING"
        # o "V BELT" sí son nombres
        letra = re.match(r"^([A-NP-UW-Z])\s+(?!RING\b)(?=[A-Z]{2,})", descripcion)
        if letra:
            descripcion, cruda = descripcion[letra.end():], cruda.lstrip()[letra.end():]
        cola = re.search(r"\s{3,}(\d{1,2})\s*$", descripcion)   # "PROTECTOR,BATTERY (170X95X3.0)        4"
        if cola and not cantidad_en_linea:
            cantidad_en_linea, descripcion = int(cola.group(1)), descripcion[:cola.start()].strip()
            cruda = descripcion
        descripcion = re.sub(r"(\s{2,}[-\d]{1,2}){2,}.*$", "", descripcion).strip(" ,")   # columnas de cantidad por versión
        # Código de modelo: lleva un número ("2TU", "7ID,8ID") o es de dos letras ("CO"); "BOLT" o "PIN" son descripciones
        es_modelo = RE_SOLO_MODELO.fullmatch(descripcion) and (re.search(r"\d", descripcion) or len(descripcion) <= 2)
        if es_modelo or RE_COLOR.match(descripcion):
            if not (filas and filas[-1]["ref"] == ref):
                continue
            descripcion = filas[-1]["descripcion"]
            cruda = descripcion
        if not re.search(r"[A-Za-z]{2}", descripcion):
            # Variante de la pieza anterior (otro código para otra versión): misma descripción.
            if not (filas and filas[-1]["ref"] == ref):
                continue
            descripcion = filas[-1]["descripcion"]
            cruda = descripcion + cruda
        resto = cruda[len(descripcion):]
        if cantidad_en_linea:
            cantidad = cantidad_en_linea
        elif re.search(r"\d", resto):
            cantidad = _cantidad(resto)
        elif i + 2 < len(lineas) and re.fullmatch(r"\(?\d{1,2}\)?", lineas[i + 2].strip()):
            cantidad = int(lineas[i + 2].strip("() \n"))
        else:
            cantidad = 1
        if descripcion.count("(") > descripcion.count(")"):
            for siguiente in lineas[i + 2:i + 5]:
                if re.fullmatch(r"\s*[^\s()]{1,12}\)\s*", siguiente):
                    descripcion = f"{descripcion}{siguiente.strip()}"
                    break
        if any(f["ref"] == ref and f["codigo"] == m.group(0)[:30] for f in filas):
            continue                                       # cada (ref, código) una sola vez por figura
        puntos = re.match(r"^\.+", descripcion)
        nivel = len(puntos.group(0)) if puntos else 0      # ".PAD SET" = pieza de un conjunto (nivel 1)
        descripcion = descripcion[nivel:].strip()
        filas.append({"ref": ref, "codigo": m.group(0)[:30], "descripcion": descripcion[:120], "nivel": nivel,
                      "cantidad": cantidad, "espanol": ""})
    return filas


def _zona_honda_hero(pagina, palabras):
    """Recorte del dibujo en las páginas Honda y Hero, o None si la página no tiene esa forma.

    Honda: el dibujo va entre el título del bloque (arriba), la tabla F.R.T. (a la derecha, desde su "Ref.") y el
    encabezado de la tabla de partes (abajo); a la izquierda queda fuera la pestaña negra con el número de grupo.
    Hero: el dibujo va a la derecha del panel con el nombre del bloque y encima de la fila "Service Item / F.R.T.".
    """
    import pymupdf
    ancho, alto = pagina.rect.width, pagina.rect.height
    servicio = [r for t, r in palabras if t.startswith("Service") and r.y0 > alto * 0.3]
    if servicio:                                                    # Hero
        y_s = min(r.y0 for r in servicio)
        panel = [r.x1 for t, r in palabras if r.x0 < ancho * 0.3 and r.y1 < y_s - 2 and re.search(r"[A-Za-z]", t)]
        izquierda = (max(panel) + 12) if panel else 0
        return pymupdf.Rect(izquierda, 0, ancho, y_s - 6)
    frt = [r for t, r in palabras if t in ("F.R.T.", "L.O.N.") and r.x0 > ancho * 0.5 and r.y0 < alto * 0.3]
    encabezado = [r for t, r in palabras if t in ("Part", "Ref.", "Ref") and r.x0 < ancho * 0.5 and r.y0 > alto * 0.3]
    if not frt or not encabezado:
        return None
    y_frt = min(r.y0 for r in frt)
    refs = [r for t, r in palabras if t.startswith("Ref") and r.x0 > ancho * 0.5 and abs(r.y0 - y_frt) < 14]
    derecha = (min(r.x0 for r in refs) if refs else min(r.x0 for r in frt) - 30) - 10
    abajo = min(r.y0 for r in encabezado) - 8
    titulo = [r for t, r in palabras if re.match(r"^[EF]-\d+", t) and r.y0 < alto * 0.2]
    arriba = (max(r.y1 for r in titulo) + 4) if titulo else 0
    izquierda = max(44, min(r.x0 for r in encabezado) - 20)        # la pestaña negra del grupo va pegada al borde
    return pymupdf.Rect(izquierda, arriba, derecha, abajo)


def _zona_dibujo(pagina):
    """Recorta la tabla de partes: si los códigos empiezan por debajo de la mitad superior, el dibujo
    es la parte de arriba; si empiezan a la derecha, es la parte izquierda. Si no, la página entera."""
    import pymupdf
    ancho, alto = pagina.rect.width, pagina.rect.height
    # Posición de los códigos de pieza en la página tal como se ve (algunas páginas vienen rotadas).
    palabras = [(_decodificar(w[4]), pymupdf.Rect(w[:4]) * pagina.rotation_matrix) for w in pagina.get_text("words")]
    zona = _zona_honda_hero(pagina, palabras)
    if zona is not None and zona.width > ancho * 0.3 and zona.height > alto * 0.2:
        return zona
    marcas = [r for t, r in palabras if RE_CODIGO.search(t)]
    if not marcas:
        return pagina.rect
    y0 = min(r.y0 for r in marcas)
    x0 = min(r.x0 for r in marcas)
    if y0 > alto * 0.35:
        return pymupdf.Rect(0, 0, ancho, y0 - 12)
    if x0 > ancho * 0.35:
        # La tabla empieza en su encabezado ("FIG.57", "REF NO."), que va a la izquierda de los códigos
        tabla = [r.x0 for t, r in palabras if r.x0 > ancho * 0.45 and (t.upper().startswith("REF") or t.upper().startswith("FIG"))
                 and r.x0 < x0]
        return pymupdf.Rect(0, 0, (min(tabla) if tabla else x0) - 10, alto)
    return pagina.rect


def _render(documento, numero_pagina):
    def hacer():
        import pymupdf
        pagina = documento[numero_pagina]
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=_zona_dibujo(pagina))
        return {"image": pix.tobytes("png"), "width": pix.width, "height": pix.height, "ext": "png"}
    return hacer


def _por_bloques(documento, re_encabezado, decodificar, numero):
    """Junta las páginas de cada figura. El dibujo es la página anterior a la primera tabla si esa
    página es de la misma figura (o no es de ninguna) y no tiene códigos; si no, la propia página."""
    paginas = []
    for pagina in documento:
        texto = pagina.get_text()
        texto = _decodificar(texto) if decodificar else texto
        lineas = texto.splitlines()
        clave = titulo = None
        for j, linea in enumerate(lineas):
            m = re_encabezado.match(linea.strip())
            if m:
                clave = m.group(1).upper()
                titulo = (m.group(2) if m.lastindex and m.lastindex >= 2 and m.group(2) else
                          (lineas[j + 1] if j + 1 < len(lineas) else "")).strip()
                if (not titulo or re_encabezado.match(titulo)) and j > 0:
                    titulo = lineas[j - 1].strip()
                break
        if "CATALOGUE NEWS" in texto.upper():
            clave = None                                   # boletines de cambios: mencionan muchos bloques, no son de ninguno
        paginas.append((clave, titulo, lineas, len(RE_CODIGO.findall(texto))))

    figuras = {}
    for n, (clave, titulo, lineas, codigos) in enumerate(paginas):
        if not clave or not codigos:
            continue
        fig = figuras.get(clave)
        if not fig:
            dibujo = n
            if n > 0:
                clave_ant, _, _, codigos_ant = paginas[n - 1]
                if codigos_ant == 0 and clave_ant in (None, clave) and (documento[n - 1].get_images()
                                                                       or documento[n - 1].get_drawings()):
                    dibujo = n - 1
            fig = figuras[clave] = {"titulo": " ".join(f"{clave} {titulo}".split()).upper(), "numero": numero(clave),
                                    "filas": [], "imagen": _render(documento, dibujo)}
        vistas = {(f["ref"], f["codigo"]) for f in fig["filas"]}
        fig["filas"].extend(f for f in _filas(lineas) if (f["ref"], f["codigo"]) not in vistas)
    return figuras


RE_BLOQUE = re.compile(r"^([EF]-\d+(?:-\d+)?)\s*$")
RE_FIG_SUZUKI = re.compile(r"^FIG\.\s*(\d+[A-Z]?)\b(?:\s*\([^)]*\))?\s*([A-Z][^\n]*)?$", re.I)


def leer_honda(documento):
    return _por_bloques(documento, RE_BLOQUE, True, _numero_bloque)


def leer_hero(documento):
    return _por_bloques(documento, RE_BLOQUE, False, _numero_bloque)


def leer_suzuki(documento):
    return _por_bloques(documento, RE_FIG_SUZUKI, False, lambda c: int(re.match(r"\d+", c).group()))


def leer_fichas(carpeta):
    carpeta = Path(carpeta)
    datos = json.loads((carpeta / "fichas.json").read_text(encoding="utf-8"))
    figuras = {}
    for n, (clave, sec) in enumerate(datos["secciones"].items(), start=1):
        if not sec.get("imagen"):
            continue

        def hacer(ruta=carpeta / sec["imagen"]):
            import pymupdf
            pix = pymupdf.Pixmap(str(ruta))
            return {"image": ruta.read_bytes(), "width": pix.width, "height": pix.height, "ext": "png"}

        filas = []
        for p in sec["partes"]:
            if not p["ref"].isdigit():
                continue
            filas.append({"ref": int(p["ref"]), "codigo": p["codigo"][:30], "descripcion": p["descripcion"][:120],
                          "nivel": 0, "cantidad": int(p["cantidad"] or 1), "espanol": ""})
        figuras[clave.upper()] = {"titulo": clave.replace("-", " ").upper(), "numero": n, "filas": filas,
                                  "imagen": hacer}
    return figuras


RE_BLOQUE_AKT = re.compile(r"^([EF])-\s*(\d+[A-Z]?)\s*$")
RE_REF_AKT = re.compile(r"^[EF]\d+[A-Z]?-(\d+)[A-Z]?$")


def leer_akt(documento):
    """Catálogos AKT: una página por bloque ("E- 3", sin título), el dibujo a la izquierda y la tabla
    Ref. / PLM / Artículo (EAN) / Descripción / Cant. a la derecha, en español."""
    import pymupdf
    figuras = {}
    for pagina in documento:
        lineas = [l.strip() for l in pagina.get_text().splitlines()]
        m = next((RE_BLOQUE_AKT.match(l) for l in lineas[:3] if RE_BLOQUE_AKT.match(l)), None)
        if not m:
            continue
        clave = f"{m.group(1)}-{m.group(2)}"
        filas = []
        refs = [i for i, linea in enumerate(lineas) if RE_REF_AKT.match(linea)]
        for k, i in enumerate(refs):
            bloque = lineas[i + 1: refs[k + 1] if k + 1 < len(refs) else len(lineas)]
            codigo = ean = descripcion = None
            cantidad = 1
            for linea in bloque:
                if not linea:
                    continue
                pegado = re.fullmatch(r"(.*?\D)?(\d{13})", linea)
                if pegado:                                  # EAN solo, o código y EAN pegados ("Bomba_Freno_Del_1770014962754")
                    ean = pegado.group(2)
                    if pegado.group(1) and not codigo:
                        codigo = pegado.group(1).strip(" _-")
                elif re.fullmatch(r"\d{1,2}", linea):
                    cantidad = int(linea)                   # la cantidad es la última línea numérica
                elif not codigo and not descripcion and " " not in linea and re.search(r"\d", linea):
                    codigo = linea
                elif re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{2}", linea) and not descripcion:
                    descripcion = re.sub(r"\s+Rp$", "", linea).strip()
            if not descripcion:
                continue
            codigo = (codigo or ean or "—")[:30]
            if any(f["ref"] == int(RE_REF_AKT.match(lineas[i]).group(1)) and f["codigo"] == codigo for f in filas):
                continue
            filas.append({"ref": int(RE_REF_AKT.match(lineas[i]).group(1)), "codigo": codigo, "descripcion": descripcion[:120],
                          "nivel": 0, "cantidad": cantidad, "espanol": descripcion})
        if not filas:
            continue
        fig = figuras.setdefault(clave, {"titulo": clave, "numero": _numero_bloque(clave), "filas": [],
                                         "imagen": _render_izquierda(documento, pagina.number)})
        fig["filas"].extend(filas)
    return figuras


def _render_izquierda(documento, numero_pagina):
    """Dibujo AKT: la zona a la izquierda de la columna "Ref." de la tabla."""
    def hacer():
        import pymupdf
        pagina = documento[numero_pagina]
        refs = [w[0] for w in pagina.get_text("words") if w[4].startswith("Ref") or RE_REF_AKT.match(w[4])]
        clip = pymupdf.Rect(0, 0, min(refs) - 8, pagina.rect.height) if refs else pagina.rect
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=clip)
        return {"image": pix.tobytes("png"), "width": pix.width, "height": pix.height, "ext": "png"}
    return hacer


FORMATOS_EXTRA = {"honda": leer_honda, "hero": leer_hero, "suzuki": leer_suzuki, "fichas": leer_fichas,
                  "akt": leer_akt}
