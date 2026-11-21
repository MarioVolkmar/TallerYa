"""Captura del visor 3D en Chrome sin ventana (local). Uso: cap.py salida.png [pk] [luces 0/1]
Vistas relativas al centro de la caja de la moto, en coordenadas de la escena (x adelante, y arriba, +z derecha/escape)."""
import base64, json, sys, time
sys.path.insert(0, r"C:\dev\TallerYa\.claude\skills\optimizar-velocidad")
import medir_chrome as mc

salida = sys.argv[1]
pk = sys.argv[2] if len(sys.argv) > 2 else "10"
luces = (sys.argv[3] if len(sys.argv) > 3 else "1") == "1"
BASE = "http://127.0.0.1:8001"
# [posicion relativa, objetivo relativo, fov]
VISTAS = [
    [[-2.8, 0.6, 0], [0, 0.0, 0], 30],          # atras
    [[-1.5, 0.9, -1.4], [-0.55, -0.05, 0], 28],    # 3/4 trasera izquierda alta
    [[2.8, 0.4, 0], [0, 0.0, 0], 30],           # frente
    [[1.9, 0.25, -1.4], [0.35, 0.0, 0], 28],      # 3/4 delantera izquierda
    [[0.65, -0.05, -1.25], [0.65, -0.2, 0], 34],  # rueda delantera, lado izquierdo
    [[-0.68, -0.05, -1.25], [-0.68, -0.2, 0], 34],  # rueda trasera, lado izquierdo
]
if len(sys.argv) > 4: VISTAS = json.load(open(sys.argv[4]))
TW, TH = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (640, 480)
JS = """(async () => {
  for (let i = 0; i < 25 && !window.__visor; i++) await new Promise(r => setTimeout(r, 200));
  if (!window.__visor) { const sc = document.querySelector('script[data-modulo]'); if (!sc) return {error: 'sin modulo ' + location.href + ' visor=' + !!document.querySelector('#visor')};
    const n = document.createElement('script'); n.type = 'module'; n.src = sc.dataset.modulo || sc.getAttribute('data-modulo'); document.body.appendChild(n); }
  for (let i = 0; i < 300 && !(window.__visor && window.__visor._moto?.raiz?.userData?.glb); i++) await new Promise(r => setTimeout(r, 200));
  const v = window.__visor; if (!v) return {error: 'sin visor'};
  document.querySelector('#visor [data-modo="moto"]')?.click();
  await new Promise(r => setTimeout(r, 3500));
  if (LUCES) v.vivo(true, false);
  await new Promise(r => setTimeout(r, 800));
  v._ctl.enableDamping = false; v._ctl.autoRotate = false;
  const caja = new v._moto.raiz.constructor.prototype.constructor === undefined ? null : null;
  const B = {min: {x: 1e9, y: 1e9, z: 1e9}, max: {x: -1e9, y: -1e9, z: -1e9}};
  v._moto.raiz.updateMatrixWorld(true);
  v._moto.raiz.traverse(o => { if (o.isMesh && o.visible && o.geometry) { o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
    for (const k of ['x','y','z']) { B.min[k] = Math.min(B.min[k], b.min[k]); B.max[k] = Math.max(B.max[k], b.max[k]); } } });
  const c = {x: (B.min.x + B.max.x) / 2, y: (B.min.y + B.max.y) / 2, z: (B.min.z + B.max.z) / 2};
  const W = TAMW, H = TAMH, NC = Math.min(3, VISTAS.length), lienzo = document.createElement("canvas"); lienzo.width = W * NC; lienzo.height = H * Math.ceil(VISTAS.length / NC);
  const g = lienzo.getContext('2d'), cv = v._ren.domElement; g.fillStyle = '#ffffff'; g.fillRect(0, 0, lienzo.width, lienzo.height);
  VISTAS.forEach(([p, t, fov], i) => {
    v._cam.fov = fov; v._cam.aspect = cv.width / cv.height; v._cam.updateProjectionMatrix();
    v._ctl.target.set(c.x + t[0], c.y + t[1], c.z + t[2]);
    v._cam.position.set(c.x + p[0], c.y + p[1], c.z + p[2]); v._ctl.update();
    v._ren.render(v._esc, v._cam);
    const s = Math.min(cv.width / W, cv.height / H), sw = W * s, sh = H * s;
    g.drawImage(cv, (cv.width - sw) / 2, (cv.height - sh) / 2, sw, sh, (i % NC) * W, Math.floor(i / NC) * H, W, H);
  });
  return {glb: v._moto.raiz.userData.glb, img: lienzo.toDataURL('image/png')};
})()"""


def main():
    cookie = mc.sesion("usuario@prueba.com")
    p, puerto, perfil = mc.abrir("d3d11")
    try:
        t = mc.pestaña(puerto)
        t("Network.enable"); t("Page.enable")
        t("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        t("Network.setCookie", name=cookie[0], value=cookie[1], url=BASE)
        t("Page.navigate", url=f"{BASE}/garaje/{pk}/")
        time.sleep(3)
        t("Runtime.evaluate", expression="document.querySelector('#visor')?.scrollIntoView()")
        js = JS.replace("LUCES", "true" if luces else "false").replace("VISTAS", json.dumps(VISTAS)).replace("TAMW", str(TW)).replace("TAMH", str(TH))
        r = t("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True, timeout=90000)
        v = r.get("result", {}).get("value") or {}
        if "img" not in v:
            print("fallo", json.dumps(r)[:400]); return
        open(salida, "wb").write(base64.b64decode(v["img"].split(",", 1)[1]))
        print("ok", v["glb"])
    finally:
        mc.cerrar(p, puerto, perfil)


main()
