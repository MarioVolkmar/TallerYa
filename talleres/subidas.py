"""Archivos públicos que suben los talleres (galería y video): se comprueba el contenido real, no el nombre ni el
Content-Type que manda el navegador (los dos los inventa quien sube), y se guardan con nombre aleatorio y la extensión
que corresponde al contenido. Así nunca queda en /media/ un .html o .svg que el navegador ejecute como página."""
import uuid

# Firma (bytes iniciales) → extensión
IMAGENES = {"jpg": lambda b: b.startswith(b"\xff\xd8\xff"), "png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
            "webp": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"}
VIDEOS = {"mp4": lambda b: b[4:8] == b"ftyp", "webm": lambda b: b.startswith(b"\x1a\x45\xdf\xa3")}
# Lo único que /media/ entrega (config/urls.py); cualquier otra extensión responde 404
EXTENSIONES_PUBLICAS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm"}


def tipo_real(archivo, permitidos):
    """Extensión según el contenido ('jpg', 'png', 'webp', 'mp4', 'webm') o None si no es de los permitidos."""
    archivo.seek(0)
    inicio = archivo.read(16)
    archivo.seek(0)
    tipo = next((ext for ext, es in permitidos.items() if es(inicio)), None)
    if tipo and permitidos is IMAGENES:
        try:  # además de la firma, que Pillow la pueda abrir (descarta archivos con cabecera falsa)
            from PIL import Image
            with Image.open(archivo) as img:
                img.verify()
        except Exception:
            return None
        finally:
            archivo.seek(0)
    return tipo


def renombrar(archivo, tipo):
    archivo.name = f"{uuid.uuid4().hex}.{tipo}"
    return archivo
