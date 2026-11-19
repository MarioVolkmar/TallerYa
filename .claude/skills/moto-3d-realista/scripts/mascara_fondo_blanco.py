"""Máscaras de fotos de estudio con fondo blanco (p. ej. cuadros de un visor 360°): umbral ∪ u2netp, con huecos rellenos.

Uso:  python -I mascara_fondo_blanco.py <carpeta_moto> v360_05 v360_14 ...   (lee <vista>/foto.jpg, escribe mascara.png)
El umbral solo pierde los paneles plateados o blancos; u2netp solo se come detalles finos. Juntos, y rellenando lo
que no toca el borde de la imagen, dan la silueta completa. Trabaja a 400 px de ancho (rápido) y reescala.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageFilter
import onnxruntime as ort
import siluetas


def rellenar(m):
    """Todo lo que no esté conectado al borde por fondo se vuelve parte de la moto (inundación sin scipy)."""
    fondo = np.zeros_like(m)
    fondo[0, :] = ~m[0, :]; fondo[-1, :] = ~m[-1, :]; fondo[:, 0] = ~m[:, 0]; fondo[:, -1] = ~m[:, -1]
    libre = ~m
    while True:
        f2 = fondo.copy()
        f2[1:] |= fondo[:-1]; f2[:-1] |= fondo[1:]; f2[:, 1:] |= fondo[:, :-1]; f2[:, :-1] |= fondo[:, 1:]
        f2 &= libre
        if (f2 == fondo).all():
            return ~fondo
        fondo = f2


def main(argv):
    carpeta = Path(argv[0])
    ses = ort.InferenceSession(str(siluetas.MODELO), providers=["CPUExecutionProvider"])
    for vista in argv[1:]:
        im = Image.open(carpeta / vista / "foto.jpg").convert("RGB"); W, H = im.size
        chica = im.resize((400, round(400 * H / W)))
        a = np.asarray(chica).astype(int)
        umbral = (a.min(2) < 232) | ((a.max(2) - a.min(2)) > 18)
        m = rellenar(umbral | siluetas.mascara(ses, chica))
        (Image.fromarray(m.astype(np.uint8) * 255).resize((W, H), Image.BILINEAR).filter(ImageFilter.MedianFilter(5))
         .point(lambda v: 255 if v > 127 else 0).save(carpeta / vista / "mascara.png"))
        print(f"{vista}: {m.mean():.1%}")


if __name__ == "__main__":
    main(sys.argv[1:])
