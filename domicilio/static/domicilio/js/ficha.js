// Ficha del mecánico a domicilio: ventanas (solicitar visita, reseña) y visor de fotos de trabajos.
// Mismo comportamiento que el detalle del taller (talleres/detalle.html), en archivo aparte.
(function () {
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-abrir]");
    if (b) {
      var d = document.getElementById(b.dataset.abrir);
      if (!d) return;
      if (b.dataset.servicio) {
        var sel = d.querySelector('select[name="servicio"]');
        if (sel) sel.value = b.dataset.servicio;
      }
      var otra = document.querySelector("dialog[open]");
      if (otra && otra !== d) otra.close();
      if (!d.open) { d.showModal(); d.abiertoEn = Date.now(); }
      return;
    }
    var abierto = e.target.closest("dialog[open]");
    if (e.target.closest("[data-cerrar]") && abierto) { abierto.close(); return; }
    if (e.target.tagName === "DIALOG" && Date.now() - (e.target.abiertoEn || 0) > 500) e.target.close();
  });

  // La solicitud de visita lleva a la página de la visita (con el botón de WhatsApp): no hace falta cerrar nada

  // Si la reseña volvió con errores, la ventana se abre otra vez
  var datos = document.getElementById("dom-ficha");
  var resena = document.getElementById("dialogo-resena");
  if (datos && datos.dataset.abrirResena && resena) resena.showModal();

  // Visor de fotos de trabajos
  var visor = document.getElementById("visor-fotos");
  if (!visor) return;
  var fotos = Array.prototype.map.call(document.querySelectorAll(".perfil-franja [data-src]"), function (f) { return f.dataset.src; });
  var actual = 0;
  function mostrar(i) {
    actual = (i + fotos.length) % fotos.length;
    document.getElementById("visor-fotos-img").src = fotos[actual];
    document.getElementById("visor-fotos-texto").textContent = (actual + 1) + " de " + fotos.length;
  }
  document.addEventListener("click", function (e) {
    var f = e.target.closest("[data-foto]");
    if (f) { mostrar(Number(f.dataset.foto)); visor.showModal(); return; }
    var paso = e.target.closest("[data-paso]");
    if (paso) mostrar(actual + Number(paso.dataset.paso));
  });
  visor.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") mostrar(actual + 1);
    if (e.key === "ArrowLeft") mostrar(actual - 1);
  });
})();
