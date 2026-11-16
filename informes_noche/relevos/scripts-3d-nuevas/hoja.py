import sys, glob, os
from PIL import Image
base = r"C:\Users\volkm\OneDrive\Desktop\TallerYa\manual_despiece"
for m in sys.argv[1:]:
    fs = sorted(glob.glob(os.path.join(base, m, "fotos", "*.jpg")))
    fs = [f for f in fs if not f.endswith("_hoja.jpg")]
    ims = [Image.open(f).convert("RGB") for f in fs]
    th = []
    for im in ims:
        im.thumbnail((300, 220)); th.append(im)
    W = 300 * len(th); hoja = Image.new("RGB", (W, 220), "white")
    for i, im in enumerate(th): hoja.paste(im, (i * 300, 0))
    hoja.save(os.path.join(base, m, "fotos", "_hoja.jpg"), quality=80)
    print(m, len(th))
