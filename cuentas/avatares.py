"""Avatares prediseñados de TallerYa (dibujos propios en SVG) y cómo pintar el avatar de una cuenta."""
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Figuras sobre un lienzo de 64x64, dentro de la zona segura 9-55 para que todas pesen lo mismo.
# Marcadores: {c} color de la figura, {a} acento, {f} fondo (para huecos), {o} tinta oscura.
O = "#111517"
CASCO = ('<path d="M14 40c0-14 9-24 21-24 10 0 17 8 17 18v6c0 2.2-1.8 4-4 4H18c-2.2 0-4-1.8-4-4z" fill="{c}"/>'
         '<path d="M34 23c8 0 14 4 17 11H35c-2.2 0-4-1.8-4-4v-4c0-1.7 1.3-3 3-3z" fill="{o}" opacity=".85"/>'
         '<path d="M37 27h8" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".45"/>'
         '<path d="M18 29c3-6 8-10 14-11" stroke="{a}" stroke-width="4" fill="none" stroke-linecap="round"/>'
         '<rect x="14" y="40" width="38" height="4" rx="2" fill="{o}" opacity=".3"/>')
FIGURAS = {
    "chispa": ('<rect x="29" y="7" width="6" height="5" rx="1.5" fill="#d3d1c7"/><rect x="30.2" y="12" width="3.6" height="3" fill="#9a9fa2"/>'
               '<path d="M24 15h16l2 23H22z" fill="#ede3cc"/><path d="M24 15h6l-1.2 23H22z" fill="#fff" opacity=".55"/>'
               '<path d="M23.6 20h16.8M23.2 25h17.6" stroke="#b9b6aa" stroke-width="1.2"/>'
               '<rect x="22.5" y="27.5" width="19" height="10.5" rx="5.2" fill="{o}"/>'
               '<rect x="26.6" y="30.6" width="3.8" height="4.4" rx="1.3" fill="{a}"/><rect x="33.6" y="30.6" width="3.8" height="4.4" rx="1.3" fill="{a}"/>'
               '<polygon points="18,40 46,40 50,46 46,52 18,52 14,46" fill="#8f9496"/>'
               '<polygon points="18,40 32,40 32,52 18,52 14,46" fill="#c4c9cc"/>'
               '<rect x="20" y="52" width="24" height="3" rx="1" fill="#f2611d"/>'),
    "llave": ('<path d="M19 45l18-18" stroke="{c}" stroke-width="8" stroke-linecap="round"/>'
              '<circle cx="41" cy="23" r="10" fill="{c}"/>'
              '<rect x="38" y="9" width="6" height="15" rx="1.5" fill="{f}" transform="rotate(45 41 23)"/>'
              '<circle cx="19" cy="45" r="2.2" fill="{f}"/>'),
    "piston": ('<rect x="19" y="11" width="26" height="19" rx="3" fill="{c}"/>'
               '<path d="M19 16h26" stroke="{o}" stroke-width="2"/><path d="M19 20h26" stroke="{a}" stroke-width="2"/>'
               '<circle cx="32" cy="25" r="2.6" fill="{o}"/>'
               '<path d="M27 30h10l-2 13h-6z" fill="{c}"/>'
               '<circle cx="32" cy="47" r="6" fill="none" stroke="{c}" stroke-width="4"/>'),
    "bujia": ('<rect x="29" y="8" width="6" height="5" rx="1.5" fill="#c4c9cc"/>'
              '<path d="M27 13h10v10H27z" fill="#ede3cc"/>'
              '<path d="M27 16.5h10M27 19.5h10" stroke="{o}" stroke-width="1.2" opacity=".35"/>'
              '<path d="M24 23h16l-1 9H25z" fill="{c}"/>'
              '<rect x="27" y="32" width="10" height="11" fill="#c4c9cc"/>'
              '<path d="M27 35h10M27 38h10M27 41h10" stroke="{o}" stroke-width="1.2" opacity=".4"/>'
              '<path d="M32 43v5h5" stroke="#c4c9cc" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
              '<path d="M41 49l4-3-1 4 4-2" stroke="{a}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
    "rueda": ('<circle cx="32" cy="32" r="18" fill="none" stroke="{c}" stroke-width="7"/>'
              '<circle cx="32" cy="32" r="18" fill="none" stroke="{o}" stroke-width="7" stroke-dasharray="2 4.3" opacity=".25"/>'
              '<circle cx="32" cy="32" r="12" fill="none" stroke="{c}" stroke-width="2"/>'
              '<path d="M32 32V20M32 32l11.4-3.7M32 32l7 9.7M32 32l-7 9.7M32 32l-11.4-3.7" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>'
              '<circle cx="32" cy="32" r="4.5" fill="{a}"/>'),
    "montana": ('<circle cx="43" cy="21" r="6" fill="{a}"/>'
                '<path d="M9 48l15-21 8 10 6-6 17 17z" fill="{c}"/>'
                '<path d="M24 27l-4.4 6.2 3-1 1.6 2 1.8-2 2.4.9z" fill="#fff" opacity=".9"/>'
                '<path d="M25 48c4-6 9-7 13 0z" fill="#f2611d"/>'),
    "moto": ('<circle cx="17" cy="42" r="8" fill="none" stroke="{c}" stroke-width="4"/><circle cx="17" cy="42" r="2" fill="{c}"/>'
             '<circle cx="47" cy="42" r="8" fill="none" stroke="{c}" stroke-width="4"/><circle cx="47" cy="42" r="2" fill="{c}"/>'
             '<path d="M17 42l8-12h14l8 12" stroke="{c}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             '<path d="M22 30l4-5h11l4 5z" fill="{c}"/>'
             '<path d="M41 30l3-8h5" stroke="{c}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             '<rect x="27" y="32" width="10" height="8" rx="2" fill="{c}"/>'
             '<path d="M22 40h14" stroke="{a}" stroke-width="3" stroke-linecap="round"/>'),
    "scooter": ('<circle cx="19" cy="45" r="6" fill="none" stroke="{c}" stroke-width="4"/>'
                '<circle cx="47" cy="45" r="6" fill="none" stroke="{c}" stroke-width="4"/>'
                '<path d="M11 43c0-8 5-12 12-12h9c3 0 5 2 6 5l2 7z" fill="{c}"/>'
                '<rect x="14" y="24" width="16" height="5" rx="2.5" fill="{c}"/>'
                '<path d="M40 43l4-24M40 18h9" stroke="{c}" stroke-width="4" stroke-linecap="round"/>'
                '<circle cx="45" cy="25" r="2.6" fill="{a}"/>'),
    "velocimetro": ('<path d="M14 42a18 18 0 0 1 36 0" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
                    '<path d="M47.6 33a18 18 0 0 1 2.4 9" fill="none" stroke="{a}" stroke-width="5" stroke-linecap="round"/>'
                    '<path d="M19.9 35l2.6 1.5M25 29.9l1.5 2.6M32 28v3M39 29.9l-1.5 2.6M44.1 35l-2.6 1.5" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>'
                    '<path d="M32 42l9.2-9.2" stroke="{a}" stroke-width="3.5" stroke-linecap="round"/>'
                    '<circle cx="32" cy="42" r="4.5" fill="{c}"/><circle cx="32" cy="42" r="1.6" fill="{o}"/>'
                    '<rect x="26" y="47" width="12" height="4" rx="1.5" fill="{c}" opacity=".45"/>'),
    "aceite": ('<path d="M32 10c6 9 13 16 13 26a13 13 0 0 1-26 0c0-10 7-17 13-26z" fill="{c}"/>'
               '<path d="M25 37a7 7 0 0 0 5 7" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity=".55"/>'
               '<circle cx="41" cy="52" r="2" fill="{a}" opacity=".6"/>'),
    "cadena": ('<g transform="rotate(-30 32 32)">'
               '<rect x="9" y="25" width="22" height="14" rx="7" fill="none" stroke="{c}" stroke-width="4"/>'
               '<rect x="33" y="25" width="22" height="14" rx="7" fill="none" stroke="{c}" stroke-width="4"/>'
               '<rect x="21" y="25" width="22" height="14" rx="7" fill="none" stroke="{a}" stroke-width="4"/>'
               '<circle cx="16" cy="32" r="2.4" fill="{c}"/><circle cx="48" cy="32" r="2.4" fill="{c}"/></g>'),
    "pinon": (''.join(f'<rect x="29.3" y="10" width="5.4" height="8" rx="1.2" fill="{{c}}" transform="rotate({g} 32 32)"/>'
                      for g in range(0, 360, 30)) +
              '<circle cx="32" cy="32" r="16" fill="{c}"/>'
              '<circle cx="32" cy="32" r="9.5" fill="none" stroke="{a}" stroke-width="1.5" opacity=".25"/>'
              '<circle cx="32" cy="32" r="5.5" fill="{f}"/>'
              '<circle cx="32" cy="21.5" r="2" fill="{f}"/><circle cx="42.5" cy="32" r="2" fill="{f}"/>'
              '<circle cx="32" cy="42.5" r="2" fill="{f}"/><circle cx="21.5" cy="32" r="2" fill="{f}"/>'),
    "bandera": ('<path d="M18 13v40" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
                '<circle cx="18" cy="12" r="2.6" fill="{a}"/>'
                '<rect x="20" y="15" width="28" height="21" rx="1" fill="{c}"/>'
                '<path d="M20 15h7v7h-7zM34 15h7v7h-7zM27 22h7v7h-7zM41 22h7v7h-7zM20 29h7v7h-7zM34 29h7v7h-7z" fill="{o}"/>'),
    "llama": ('<path d="M32 9c2 8 12 12 12 25a12 12 0 0 1-24 0c0-6 3-10 6-13 1 4 3 6 5 6-1-6-1-12 1-18z" fill="{c}"/>'
              '<path d="M32 28c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11z" fill="{a}"/>'
              '<path d="M32 36c1.5 2 2.5 3 2.5 4.5a2.5 2.5 0 0 1-5 0c0-1.5 1-2.5 2.5-4.5z" fill="#fff" opacity=".85"/>'),
    "rayo": ('<path d="M39 11L19 38h13l-4 18 21-29H36z" fill="{o}" opacity=".25"/>'
             '<path d="M37 9L17 36h13l-4 18 21-29H34z" fill="{c}"/>'
             '<path d="M33 15L22 31" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".45"/>'),
    "gafas": ('<rect x="6" y="30" width="52" height="5" rx="2.5" fill="{o}" opacity=".45"/>'
              '<path d="M10 30c0-4 3-7 7-7h30c4 0 7 3 7 7v4c0 5-4 8-8 8h-6c-3 0-5-4-8-4s-5 4-8 4h-6c-4 0-8-3-8-8z" fill="{c}"/>'
              '<ellipse cx="22" cy="33" rx="7.5" ry="5.5" fill="{o}"/><ellipse cx="42" cy="33" rx="7.5" ry="5.5" fill="{o}"/>'
              '<path d="M17 32l4-3M37 32l4-3" stroke="{a}" stroke-width="2.2" stroke-linecap="round"/>'),
    "carretera": ('<circle cx="46" cy="17" r="5" fill="{a}"/>'
                  '<path d="M17 53L29 13h6l12 40z" fill="{o}"/>'
                  '<path d="M17 53L29 13M47 53L35 13" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>'
                  '<path d="M32 17v4M32 26v6M32 38v9" stroke="{a}" stroke-width="2.5" stroke-linecap="round"/>'),
    "escape": ('<path d="M8 35h14" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
               '<rect x="19" y="28" width="26" height="14" rx="7" fill="{c}"/>'
               '<path d="M27 31v8M32 31v8M37 31v8" stroke="{o}" stroke-width="1.6" opacity=".3"/>'
               '<rect x="43" y="31" width="10" height="8" rx="2" fill="{c}"/><circle cx="53" cy="35" r="3" fill="{o}"/>'
               '<circle cx="51" cy="24" r="3" fill="{a}" opacity=".55"/><circle cx="55" cy="17" r="4" fill="{a}" opacity=".35"/>'),
}

# Chispa con un rayito saliendo a su lado (la cabeza un poco a la izquierda para dejarle sitio al rayo)
FIGURAS["chispa-rayito"] = ('<g transform="translate(-5 0)">' + FIGURAS["chispa"] + '</g>'
                            '<path d="M49 13l-7 11h5l-3 9 8-12h-5z" fill="{a}"/>'
                            '<path d="M47.5 16l-3.5 6" stroke="#fff" stroke-width="1.3" stroke-linecap="round" opacity=".6"/>')

# Catálogo: clave -> (nombre, figura, color de la figura, fondo, acento)
PREDISENADOS = {
    "chispa": ("Chispa", "chispa", "#ede3cc", "#1d2427", "#e3a72f"),
    "chispa-rayos": ("Chispa rayos X", "chispa", "#ede3cc", "#12324d", "#85b7eb"),
    "chispa-rayito": ("Chispa con rayito", "chispa-rayito", "#ede3cc", "#252e31", "#e3a72f"),
    "casco-lava": ("Casco lava", "casco", "#f2611d", "#1d2427", "#ede3cc"),
    "llave": ("Llave", "llave", "#ede3cc", "#f2611d", "#1d2427"),
    "piston": ("Pistón", "piston", "#e3a72f", "#1d2427", "#f2611d"),
    "bujia": ("Bujía", "bujia", "#f2611d", "#252e31", "#e3a72f"),
    "rueda": ("Rueda", "rueda", "#ede3cc", "#3a7bd5", "#f2611d"),
    "montana": ("TallerYa", "montana", "#ede3cc", "#1f3a36", "#e3a72f"),
    "moto": ("Moto", "moto", "#ede3cc", "#f2611d", "#1d2427"),
    "scooter": ("Scooter", "scooter", "#1d2427", "#e3a72f", "#ede3cc"),
    "velocimetro": ("Velocímetro", "velocimetro", "#ede3cc", "#1d2427", "#f2611d"),
    "aceite": ("Aceite", "aceite", "#e3a72f", "#252e31", "#e3a72f"),
    "cadena": ("Cadena", "cadena", "#c4c9cc", "#1f3a36", "#e3a72f"),
    "pinon": ("Piñón", "pinon", "#ede3cc", "#8a5cd6", "#1d2427"),
    "bandera": ("Meta", "bandera", "#ede3cc", "#3fbf6b", "#f2611d"),
    "llama": ("Llama", "llama", "#f2611d", "#1d2427", "#e3a72f"),
    "rayo": ("Rayo", "rayo", "#e3a72f", "#3a7bd5", "#e3a72f"),
    "gafas": ("Gafas", "gafas", "#ede3cc", "#c0392b", "#e3a72f"),
    "carretera": ("Carretera", "carretera", "#ede3cc", "#1f3a36", "#e3a72f"),
    "escape": ("Escape", "escape", "#c4c9cc", "#252e31", "#c4c9cc"),
}

# Avatares que ya no se ofrecen pero que algunas cuentas pueden tener elegidos: se siguen mostrando.
ANTERIORES = {
    "casco-crema": ("Casco crema", "casco", "#ede3cc", "#1f3a36", "#f2611d"),
    "casco-azul": ("Casco azul", "casco", "#3a7bd5", "#1d2427", "#ede3cc"),
    "casco-verde": ("Casco verde", "casco", "#3fbf6b", "#252e31", "#ede3cc"),
    "casco-morado": ("Casco morado", "casco", "#8a5cd6", "#252e31", "#ede3cc"),
}


def svg_predisenado(clave, tam=40):
    nombre, figura, color, fondo, acento = PREDISENADOS.get(clave) or ANTERIORES[clave]
    dibujo = CASCO if figura == "casco" else FIGURAS[figura]
    for marca, valor in (("{c}", color), ("{a}", acento), ("{f}", fondo), ("{o}", O)):
        dibujo = dibujo.replace(marca, valor)
    return mark_safe(
        f'<svg viewBox="0 0 64 64" width="{tam}" height="{tam}" class="avatar" role="img" aria-label="{nombre}">'
        f'<circle cx="32" cy="32" r="32" fill="{fondo}"/>'
        f'<circle cx="32" cy="32" r="30.5" fill="none" stroke="#fff" stroke-opacity=".1" stroke-width="2"/>'
        f'{dibujo}</svg>'
    )


def html_avatar(usuario, tam=40):
    """Foto subida, avatar prediseñado o la inicial del nombre (en ese orden)."""
    perfil = getattr(usuario, "perfil", None) if usuario and usuario.is_authenticated else None
    if perfil and perfil.avatar_foto:
        return format_html('<img src="{}" width="{}" height="{}" class="avatar" alt="" loading="lazy">',
                           perfil.avatar_foto.url, tam, tam)
    if perfil and (perfil.avatar_predisenado in PREDISENADOS or perfil.avatar_predisenado in ANTERIORES):
        return svg_predisenado(perfil.avatar_predisenado, tam)
    nombre = (getattr(usuario, "first_name", "") or getattr(usuario, "email", "") or "?").strip()
    return format_html('<span class="avatar avatar-inicial" style="width:{}px;height:{}px;font-size:{}px" aria-hidden="true">{}</span>',
                       tam, tam, round(tam * 0.45), nombre[:1].upper() or "?")
