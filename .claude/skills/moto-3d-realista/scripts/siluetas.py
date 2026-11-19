"""Silueta (máscara blanco/negro) de cada foto de referencia con U^2-Net pequeño (u2netp.onnx, 4,6 MB).

Uso:  python -I siluetas.py <carpeta_moto>   (busca <carpeta_moto>/*/foto.jpg y escribe mascara.png al lado)
      opcional: --modelo ruta/u2netp.onnx  --caja x0,y0,x1,y1 (recorta a esa caja relativa 0-1 antes, para fotos con gente)
Se queda con el componente conectado más grande que toque el centro de la caja de la moto.
Las fotos solo se leen (referencia de silueta); nunca se redistribuyen ni se usan como textura.
"""
import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import onnxruntime as ort

RAIZ = Path(__file__).resolve().parents[4]  # .../TallerYa
MODELO = RAIZ / "modelos_3d_local/_herramientas/u2netp/u2netp.onnx"


def mascara(ses, im):
    x = np.asarray(im.convert("RGB").resize((320, 320), Image.BILINEAR), np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    s = ses.run(None, {ses.get_inputs()[0].name: x})[0][0, 0]
    s = (s - s.min()) / (s.max() - s.min() + 1e-9)
    return np.asarray(Image.fromarray((s * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR)) > 127


def mayor_componente(m):
    """Componente conectado (4-vecinos) más grande, sin scipy."""
    h, w = m.shape
    etiqueta = np.zeros((h, w), np.int32); mejor, tam_mejor, actual = 0, 0, 0
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if etiqueta[y0, x0]:
            continue
        actual += 1; pila = [(y0, x0)]; etiqueta[y0, x0] = actual; n = 0
        while pila:
            y, x = pila.pop(); n += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not etiqueta[yy, xx]:
                    etiqueta[yy, xx] = actual; pila.append((yy, xx))
        if n > tam_mejor:
            mejor, tam_mejor = actual, n
    return etiqueta == mejor


def main(argv):
    carpeta = Path(argv[0]); cajas = {}
    if "--cajas" in argv:  # json {"subcarpeta": [x0,y0,x1,y1]} relativo
        cajas = json.loads(Path(argv[argv.index("--cajas") + 1]).read_text())
    ses = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
    for foto in sorted(carpeta.glob("*/foto.jpg")):
        im = Image.open(foto); W, H = im.size
        caja = cajas.get(foto.parent.name)
        if caja:
            x0, y0, x1, y1 = (int(round(c * d)) for c, d in zip(caja, (W, H, W, H)))
            sub = im.crop((x0, y0, x1, y1)); m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = mascara(ses, sub)
        else:
            m = mascara(ses, im)
        small = Image.fromarray(m.astype(np.uint8) * 255).resize((W // 4, H // 4), Image.NEAREST)
        mc = mayor_componente(np.asarray(small) > 127)
        m = np.asarray(Image.fromarray(mc.astype(np.uint8) * 255).resize((W, H), Image.NEAREST)) > 127
        Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MedianFilter(5)).save(foto.parent / "mascara.png")
        print(f"{foto.parent.name}: {m.mean():.1%} de la foto")


if __name__ == "__main__":
    main(sys.argv[1:])
