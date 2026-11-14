"""Avatares prediseñados de TallerYa (dibujos propios en SVG) y cómo pintar el avatar de una cuenta."""
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Fondo y figura de cada avatar. Las figuras se dibujan sobre un lienzo de 64x64.
CASCO = ('<path d="M14 38c0-12 8-21 19-21s19 8 19 19v6H30l-4 6H16z" fill="{c}"/>'
         '<path d="M33 25c8 0 13 5 14 11H33z" fill="#111517" opacity=".85"/>'
         '<path d="M16 44h12l4-6h20v3c0 2-1 3-3 3H31l-4 6H18c-2 0-3-1-3-3z" fill="#0b0e0f" opacity=".35"/>')
FIGURAS = {
    "llave": '<path d="M41 13a10 10 0 0 0-12 13L14 41a4 4 0 0 0 6 6l15-15a10 10 0 0 0 13-12l-6 6-6-1-1-6z" fill="{c}"/>',
    "piston": ('<rect x="20" y="12" width="24" height="18" rx="4" fill="{c}"/>'
               '<path d="M20 18h24M20 23h24" stroke="#111517" stroke-width="2.5"/>'
               '<path d="M28 30l-3 12M36 30l3 12" stroke="{c}" stroke-width="4" stroke-linecap="round"/>'
               '<circle cx="32" cy="47" r="6" fill="none" stroke="{c}" stroke-width="4"/>'),
    "bujia": ('<rect x="27" y="10" width="10" height="9" rx="2" fill="#ede3cc"/>'
              '<rect x="24" y="19" width="16" height="13" rx="2" fill="{c}"/>'
              '<rect x="28" y="32" width="8" height="12" fill="#c4c9cc"/><path d="M32 44v7h6" stroke="#c4c9cc" stroke-width="3" fill="none"/>'),
    "rueda": ('<circle cx="32" cy="32" r="19" fill="none" stroke="{c}" stroke-width="7"/>'
              '<circle cx="32" cy="32" r="5" fill="{c}"/>'
              '<path d="M32 18v9M32 37v9M18 32h9M37 32h9M22 22l6 6M36 36l6 6M42 22l-6 6M28 36l-6 6" stroke="{c}" stroke-width="2.5"/>'),
    "montana": ('<circle cx="42" cy="20" r="7" fill="#e3a72f"/><path d="M8 50l14-20 8 10 8-7 18 17z" fill="{c}"/>'
                '<path d="M18 50c5-6 12-5 9 0z" fill="#f2611d"/>'),
}
FIGURAS.update({
    "moto": ('<circle cx="17" cy="42" r="8" fill="none" stroke="{c}" stroke-width="4"/>'
             '<circle cx="47" cy="42" r="8" fill="none" stroke="{c}" stroke-width="4"/>'
             '<path d="M17 42l9-13h12l4 6h-9l-4 7M38 29l3-7h5M42 35l5 7" stroke="{c}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             '<path d="M26 26h9l2 3H24z" fill="{c}"/>'),
    "scooter": ('<circle cx="18" cy="45" r="6" fill="none" stroke="{c}" stroke-width="4"/><circle cx="46" cy="45" r="6" fill="none" stroke="{c}" stroke-width="4"/>'
                '<path d="M12 42c0-7 5-11 12-11h8c3 0 4 2 5 5l2 6z" fill="{c}"/>'
                '<path d="M39 42l4-24" stroke="{c}" stroke-width="4" stroke-linecap="round"/>'
                '<path d="M39 17h9" stroke="{c}" stroke-width="4" stroke-linecap="round"/>'
                '<rect x="16" y="25" width="13" height="5" rx="2.5" fill="{c}"/>'),
    "velocimetro": ('<path d="M12 42a20 20 0 0 1 40 0" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
                    '<path d="M16 34l3 2M22 26l2 3M32 22v4M42 26l-2 3M48 34l-3 2" stroke="{c}" stroke-width="2.5" stroke-linecap="round"/>'
                    '<path d="M32 42l11-12" stroke="#f2611d" stroke-width="4" stroke-linecap="round"/><circle cx="32" cy="42" r="4" fill="{c}"/>'),
    "aceite": ('<path d="M32 12c7 10 13 17 13 25a13 13 0 0 1-26 0c0-8 6-15 13-25z" fill="{c}"/>'
               '<path d="M26 38a6 6 0 0 0 6 6" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" opacity=".6"/>'),
    "cadena": ('<rect x="10" y="24" width="18" height="16" rx="8" fill="none" stroke="{c}" stroke-width="4"/>'
               '<rect x="23" y="24" width="18" height="16" rx="8" fill="none" stroke="{c}" stroke-width="4" opacity=".75"/>'
               '<rect x="36" y="24" width="18" height="16" rx="8" fill="none" stroke="{c}" stroke-width="4"/>'),
    "pinon": ('<circle cx="32" cy="32" r="14" fill="{c}"/><circle cx="32" cy="32" r="5" fill="#111517"/>'
              '<path d="M32 12v6M32 46v6M12 32h6M46 32h6M18 18l4 4M42 42l4 4M46 18l-4 4M22 42l-4 4" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'),
    "bandera": ('<path d="M18 12v40" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
                '<rect x="20" y="14" width="28" height="20" fill="{c}"/>'
                '<path d="M20 14h7v5h-7zM34 14h7v5h-7zM27 19h7v5h-7zM41 19h7v5h-7zM20 24h7v5h-7zM34 24h7v5h-7zM27 29h7v5h-7zM41 29h7v5h-7z" fill="#111517"/>'),
    "llama": ('<path d="M32 10c3 9 13 13 13 25a13 13 0 0 1-26 0c0-7 4-11 7-14 0 5 2 7 4 8 0-7 0-13 2-19z" fill="{c}"/>'
              '<path d="M32 30c3 4 6 6 6 10a6 6 0 0 1-12 0c0-3 3-6 6-10z" fill="#e3a72f"/>'),
    "rayo": '<path d="M36 10L18 36h12l-4 18 20-28H34z" fill="{c}"/>',
    "gafas": ('<path d="M10 30c0-4 3-6 7-6h30c4 0 7 2 7 6v4c0 5-4 8-8 8h-6c-3 0-5-4-8-4s-5 4-8 4h-6c-4 0-8-3-8-8z" fill="{c}"/>'
              '<ellipse cx="22" cy="33" rx="7" ry="5" fill="#111517" opacity=".8"/><ellipse cx="42" cy="33" rx="7" ry="5" fill="#111517" opacity=".8"/>'
              '<path d="M18 31l3-2M38 31l3-2" stroke="#ffffff" stroke-width="2" stroke-linecap="round" opacity=".7"/>'),
    "carretera": ('<path d="M24 52l6-40h4l6 40z" fill="{c}"/>'
                  '<path d="M32 16v5M32 26v6M32 37v7" stroke="#e3a72f" stroke-width="2.5" stroke-linecap="round"/>'
                  '<circle cx="47" cy="17" r="5" fill="#e3a72f"/>'),
    "escape": ('<path d="M10 38h26l10-6h8v14h-8l-10-4H10z" fill="{c}"/>'
               '<circle cx="54" cy="39" r="4" fill="#111517"/>'
               '<path d="M14 30c3-3 0-5 3-8M22 30c3-3 0-5 3-8" stroke="{c}" stroke-width="2.5" fill="none" stroke-linecap="round" opacity=".6"/>'),
})
FONDOS = {"lava": "#f2611d", "mostaza": "#e3a72f", "crema": "#ede3cc", "verde": "#3fbf6b", "azul": "#3a7bd5",
          "morado": "#8a5cd6"}

# Catálogo: clave -> (nombre, figura, color de la figura, fondo)
PREDISENADOS = {
    "casco-lava": ("Casco lava", "casco", "#f2611d", "#1d2427"),
    "llave": ("Llave", "llave", "#ede3cc", "#f2611d"),
    "piston": ("Pistón", "piston", "#e3a72f", "#1d2427"),
    "bujia": ("Bujía", "bujia", "#f2611d", "#252e31"),
    "rueda": ("Rueda", "rueda", "#ede3cc", "#3a7bd5"),
    "montana": ("TallerYa", "montana", "#ede3cc", "#1f3a36"),
    "moto": ("Moto", "moto", "#ede3cc", "#f2611d"),
    "scooter": ("Scooter", "scooter", "#1d2427", "#e3a72f"),
    "velocimetro": ("Velocímetro", "velocimetro", "#ede3cc", "#1d2427"),
    "aceite": ("Aceite", "aceite", "#e3a72f", "#252e31"),
    "cadena": ("Cadena", "cadena", "#c4c9cc", "#1f3a36"),
    "pinon": ("Piñón", "pinon", "#ede3cc", "#8a5cd6"),
    "bandera": ("Meta", "bandera", "#ede3cc", "#3fbf6b"),
    "llama": ("Llama", "llama", "#f2611d", "#1d2427"),
    "rayo": ("Rayo", "rayo", "#e3a72f", "#3a7bd5"),
    "gafas": ("Gafas", "gafas", "#ede3cc", "#c0392b"),
    "carretera": ("Carretera", "carretera", "#3a4447", "#1f3a36"),
    "escape": ("Escape", "escape", "#c4c9cc", "#252e31"),
}

# Avatares que ya no se ofrecen pero que algunas cuentas pueden tener elegidos: se siguen mostrando.
ANTERIORES = {
    "casco-crema": ("Casco crema", "casco", "#ede3cc", "#1f3a36"),
    "casco-azul": ("Casco azul", "casco", "#3a7bd5", "#1d2427"),
    "casco-verde": ("Casco verde", "casco", "#3fbf6b", "#252e31"),
    "casco-morado": ("Casco morado", "casco", "#8a5cd6", "#252e31"),
}


def svg_predisenado(clave, tam=40):
    nombre, figura, color, fondo = PREDISENADOS.get(clave) or ANTERIORES[clave]
    dibujo = (CASCO if figura == "casco" else FIGURAS[figura]).replace("{c}", color)
    return mark_safe(
        f'<svg viewBox="0 0 64 64" width="{tam}" height="{tam}" class="avatar" role="img" aria-label="{nombre}">'
        f'<rect width="64" height="64" rx="32" fill="{fondo}"/>{dibujo}</svg>'
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
