// Carga diferida del visor 3D: three.js (~670 KB) y moto3d.js se descargan solo cuando el visor está por
// aparecer en pantalla. Si ya se ve al abrir la página, se piden de una y todos en paralelo.
// Este script va justo después del visor: la descarga empieza mientras el navegador sigue leyendo el resto
// de la página, y la moto se arma cuando la página terminó de cargar (moto3d.js lee datos que vienen al final).
(function () {
  var visor = document.getElementById("visor");
  if (!visor) return;
  var script = document.currentScript;
  var modulo = script.dataset.modulo;
  var cdn = "https://cdn.jsdelivr.net/npm/three@0.160.0/";
  var librerias = [
    "build/three.module.min.js",
    "examples/jsm/controls/OrbitControls.js",
    "examples/jsm/environments/RoomEnvironment.js",
    "examples/jsm/geometries/DecalGeometry.js",
    "examples/jsm/utils/BufferGeometryUtils.js",
  ].map(function (ruta) { return cdn + ruta; });
  // Módulos propios que importa moto3d.js (sin precarga se piden en cascada: uno, luego sus importados...).
  // Van sin huella de versión, igual que como los pide moto3d.js con su import relativo.
  var carpeta = modulo.replace(/moto3d(\.[0-9a-f]+)?\.js(\?.*)?$/, "moto3d/");
  var propios = ["construir.js", "texturas.js", "geometria.js", "comun.js", "cache.js"].map(function (n) { return carpeta + n; });
  var cargado = false;

  function precargar(url, cruzado) {
    var l = document.createElement("link");
    l.rel = "modulepreload";
    l.href = url;
    if (cruzado) l.crossOrigin = "";
    document.head.appendChild(l);
  }
  function arrancar() {
    var m = document.createElement("script");
    m.type = "module";
    m.src = modulo;
    document.body.appendChild(m);
  }
  function cargar() {
    if (cargado) return;
    cargado = true;
    librerias.forEach(function (url) { precargar(url, true); });
    precargar(modulo, false);
    propios.forEach(function (url) { precargar(url, false); });
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", arrancar);
    else arrancar();
  }

  var caja = visor.getBoundingClientRect();
  // (innerHeight 0: ventana sin tamaño todavía, como una pestaña oculta; ahí el vigía no avisa, se carga de una)
  var yaSeVe = !innerHeight || (caja.top < innerHeight + 300 && caja.bottom > -300);
  if (yaSeVe || !("IntersectionObserver" in window)) return cargar();
  // Mientras espera, el aviso de "sin conexión" de la página no debe saltar
  window.__moto3dEsperando = true;
  var vigia = new IntersectionObserver(function (entradas) {
    if (entradas.some(function (e) { return e.isIntersecting; })) { vigia.disconnect(); cargar(); }
  }, { rootMargin: "300px" });
  vigia.observe(visor);
})();
