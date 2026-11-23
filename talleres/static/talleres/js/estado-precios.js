/* Interruptor «Mostrar precios»: guarda al instante sin recargar (estado_precios.html) */
(function () {
  if (window.__estadoPrecios) return; window.__estadoPrecios = true;
  function cookie(n) { var m = document.cookie.match("(?:^|; )" + n + "=([^;]*)"); return m ? decodeURIComponent(m[1]) : ""; }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-interruptor]"); if (!b) return;
    var caja = b.closest("[data-estado-precios]"), tit = caja.querySelector("[data-estado-titulo]"), res = caja.querySelector("[data-estado-resto]");
    var quiere = b.getAttribute("aria-checked") !== "true";
    b.disabled = true;
    fetch(caja.dataset.url, {
      method: "POST", credentials: "same-origin",
      headers: { "X-CSRFToken": cookie("csrftoken"), "X-Requested-With": "fetch", "Content-Type": "application/x-www-form-urlencoded" },
      body: "valor=" + (quiere ? "1" : "0")
    }).then(function (r) { if (!r.ok) throw 0; b.setAttribute("aria-checked", quiere ? "true" : "false");
      var k = quiere ? "on" : "off"; tit.textContent = caja.dataset["t" + (quiere ? "On" : "Off")]; res.textContent = "· " + caja.dataset["r" + (quiere ? "On" : "Off")]; })
      .catch(function () { res.textContent = "· No pudimos guardar. Intenta de nuevo."; })
      .then(function () { b.disabled = false; });
  });
})();
