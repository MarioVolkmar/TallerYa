// Submenús del menú principal y del avatar (base.html): se abren con clic o teclado, no con hover.
// Marcado: <div data-submenu><button aria-expanded="false" aria-controls="id">…</button><div id="id" hidden>…enlaces…</div></div>
// Escape cierra y devuelve el foco al botón; flechas arriba/abajo recorren los enlaces; clic o foco fuera cierra.
(function () {
  var menus = [].slice.call(document.querySelectorAll("[data-submenu]"));
  if (!menus.length) return;

  function partes(m) {
    var boton = m.querySelector("[aria-controls]");
    return { boton: boton, panel: document.getElementById(boton.getAttribute("aria-controls")) };
  }
  function abrir(m, si) {
    var p = partes(m);
    p.panel.hidden = !si;
    p.boton.setAttribute("aria-expanded", String(si));
  }
  function cerrarOtros(actual) { menus.forEach(function (m) { if (m !== actual) abrir(m, false); }); }
  function enlaces(panel) {
    return [].slice.call(panel.querySelectorAll("a, button")).filter(function (a) { return !a.hidden && a.offsetParent !== null; });
  }

  menus.forEach(function (m) {
    var p = partes(m);
    p.boton.addEventListener("click", function () {
      var abre = p.panel.hidden;
      cerrarOtros(m);
      abrir(m, abre);
    });
    m.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !p.panel.hidden) { abrir(m, false); p.boton.focus(); e.preventDefault(); return; }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      if (p.panel.hidden) { if (document.activeElement !== p.boton) return; cerrarOtros(m); abrir(m, true); }
      var items = enlaces(p.panel); if (!items.length) return;
      var i = items.indexOf(document.activeElement);
      var sig = i < 0 ? (e.key === "ArrowDown" ? 0 : items.length - 1) : (i + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      items[sig].focus(); e.preventDefault();
    });
    m.addEventListener("focusout", function (e) { if (e.relatedTarget && !m.contains(e.relatedTarget)) abrir(m, false); });
  });

  document.addEventListener("click", function (e) {
    menus.forEach(function (m) { if (!m.contains(e.target)) abrir(m, false); });
  });
})();
