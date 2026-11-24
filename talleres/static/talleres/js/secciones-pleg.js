/* Secciones plegables de las fichas (<details data-pleg="clave">): recuerda lo abierto/cerrado,
   cierra las largas en el celular la primera vez y abre la sección a la que apunta el # de la URL. */
(function () {
  var CLAVE = "tallerya.pleg";
  var secciones = document.querySelectorAll("details[data-pleg]");
  if (!secciones.length) return;
  var guardado = {};
  try { guardado = JSON.parse(localStorage.getItem(CLAVE)) || {}; } catch (e) { guardado = {}; }
  var celular = window.matchMedia("(max-width: 767px)").matches;

  secciones.forEach(function (d) {
    var k = d.dataset.pleg;
    if (k in guardado) d.open = !!guardado[k];
    else if (celular && d.hasAttribute("data-movil-cerrada")) d.open = false;
    d.addEventListener("toggle", function () {
      guardado[k] = d.open;
      try { localStorage.setItem(CLAVE, JSON.stringify(guardado)); } catch (e) {}
    });
  });

  function abrirAncla(desplazar) {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    var d = el && el.closest("details[data-pleg]");
    if (!d) return;
    if (!d.open) d.open = true;
    if (desplazar) el.scrollIntoView();
  }
  abrirAncla(true);
  window.addEventListener("hashchange", function () { abrirAncla(true); });
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (a && a.hash === location.hash) abrirAncla(true);
  });
})();
