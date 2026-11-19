// Arranque del visor 3D. Va con `defer` (no frena la lectura del HTML): three.js, moto3d.js y construir.js ya
// empezaron a bajar por los <link rel="modulepreload"> de la plantilla; aquí se precargan los demás módulos y,
// cuando el visor está a la vista (o por aparecer), se arranca moto3d.js.
(function () {
  var visor = document.getElementById("visor");
  if (!visor) return;
  var script = document.currentScript;
  var modulo = script.dataset.modulo;
  // three.js y sus addons salen del importmap de la página (nuestros estáticos, con su huella en producción)
  var mapa = {};
  try { mapa = JSON.parse(document.querySelector('script[type="importmap"]').textContent).imports || {}; } catch (e) {}
  var librerias = ["three", "three/addons/controls/OrbitControls.js", "three/addons/utils/BufferGeometryUtils.js"]
    .map(function (k) { return mapa[k]; }).filter(Boolean);
  // Módulos propios que importa moto3d.js (sin precarga se piden en cascada: uno, luego sus importados...).
  // Van sin huella de versión, igual que como los pide moto3d.js con su import relativo.
  var carpeta = modulo.replace(/moto3d(\.[0-9a-f]+)?\.js(\?.*)?$/, "moto3d/");
  var propios = ["construir.js", "rasgos.js", "texturas.js", "geometria.js", "comun.js", "cache.js"].map(function (n) { return carpeta + n; });
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
  // El armado del 3D ocupa la página varios segundos en un celular: arranca cuando el esquema del despiece ya se
  // pintó (o a los 2,5 s si tarda o no hay esquema), así el esquema no queda detrás. La descarga va adelantada.
  function trasEsquema() {
    var esquema = document.getElementById("despiece");
    var hecho = false;
    function seguir() {
      if (hecho) return;
      hecho = true;
      if (obs) obs.disconnect();
      requestAnimationFrame(function () { setTimeout(arrancar, 0); });
    }
    var obs = null;
    if (!esquema || esquema.classList.contains("despiece-listo") || !("MutationObserver" in window)) return seguir();
    obs = new MutationObserver(function () { if (esquema.classList.contains("despiece-listo") || esquema.classList.contains("despiece-fallo")) seguir(); });
    obs.observe(esquema, { attributes: true, attributeFilter: ["class"] });
    setTimeout(seguir, 2500);
  }
  function cargar() {
    if (cargado) return;
    cargado = true;
    (window.tyM = window.tyM || []).push(["visor_3d", { origen: "moto" }]);
    librerias.forEach(function (url) { precargar(url, false); });
    precargar(modulo, false);
    propios.forEach(function (url) { precargar(url, false); });
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", trasEsquema);
    else trasEsquema();
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
