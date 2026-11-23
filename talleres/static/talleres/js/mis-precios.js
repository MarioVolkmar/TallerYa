/* «Mis precios» (taller y mecánico): tarjetas por servicio, filas nuevas sin recargar, pesos con miles,
   validación en vivo de «hasta ≥ desde» y referencia del sector. */
(function () {
  var raiz = document.querySelector("[data-mis-precios]"); if (!raiz) return;
  var form = raiz.closest("form"), pref = raiz.dataset.prefijo;
  var total = form.querySelector("[name=" + pref + "-TOTAL_FORMS]");
  var medianas = {}; try { medianas = JSON.parse(raiz.querySelector("[data-medianas]").textContent); } catch (e) {}
  var plantilla = raiz.querySelector("[data-fila-plantilla]");
  var tarjetas = raiz.querySelector("[data-tarjetas]"), vacio = raiz.querySelector("[data-vacio]");

  function miles(v) { v = String(v).replace(/\D/g, ""); return v.replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function num(v) { return parseInt(String(v).replace(/\D/g, ""), 10); }
  function peso(n) { return "$" + miles(n); }

  function revisar(fila) {
    var d = fila.querySelector("input[name$=-desde]"), h = fila.querySelector("input[name$=-hasta]");
    var nd = num(d.value), nh = num(h.value), mal = nd >= 0 && nh >= 0 && nh < nd;
    h.setCustomValidity(mal ? "El «hasta» debe ser mayor o igual al «desde»." : "");
    fila.classList.toggle("mp-mal", mal);
    var ref = fila.querySelector("[data-ref]"), card = fila.closest("[data-card]");
    var cil = fila.querySelector("select[name$=-cilindraje]").value;
    var m = (medianas[card.dataset.servicio] || {})[cil];
    if (mal) { ref.textContent = "El «hasta» debe ser mayor o igual al «desde»."; ref.hidden = false; ref.classList.add("mp-ref-mal"); }
    else if (m) { ref.textContent = "Precio típico en Medellín: " + peso(m[0]) + " a " + peso(m[1]); ref.hidden = false; ref.classList.remove("mp-ref-mal"); }
    else { ref.hidden = true; }
  }
  function preparar(fila) {
    fila.querySelectorAll("[data-pesos], input[name$=-desde], input[name$=-hasta]").forEach(function (i) {
      i.value = miles(i.value);
      i.addEventListener("input", function () { i.value = miles(i.value); revisar(fila); });
    });
    fila.querySelector("select[name$=-cilindraje]").addEventListener("change", function () { revisar(fila); });
    revisar(fila);
  }
  function agregarFila(card) {
    var i = parseInt(total.value, 10);
    var nodo = plantilla.content.cloneNode(true).firstElementChild;
    nodo.innerHTML = nodo.innerHTML.replace(/__prefix__/g, i);
    nodo.querySelector("input[name$=-servicio]").value = card.dataset.servicio;
    total.value = i + 1;
    card.insertBefore(nodo, card.querySelector("[data-otro-cil]"));
    preparar(nodo);
    var c = nodo.querySelector("select"); if (c) c.focus();
    return nodo;
  }
  function crearCard(id, nombre) {
    var card = document.createElement("section");
    card.className = "mp-card"; card.dataset.card = ""; card.dataset.servicio = id; card.dataset.nombre = nombre;
    var h = document.createElement("h2"); h.className = "mp-card-titulo"; h.textContent = nombre; card.appendChild(h);
    var b = document.createElement("button"); b.type = "button"; b.className = "mp-mas"; b.dataset.otroCil = ""; b.textContent = "+ Otro cilindraje";
    card.appendChild(b); tarjetas.appendChild(card);
    if (vacio) vacio.hidden = true;
    return card;
  }

  raiz.querySelectorAll("[data-fila]").forEach(preparar);
  raiz.addEventListener("click", function (e) {
    var otro = e.target.closest("[data-otro-cil]");
    if (otro) { agregarFila(otro.closest("[data-card]")); return; }
    var q = e.target.closest("[data-quitar-fila]");
    if (q) {
      var fila = q.closest("[data-fila]"), card = fila.closest("[data-card]"); fila.remove();
      if (!card.querySelector("[data-fila]")) { card.remove(); if (vacio && !tarjetas.children.length) vacio.hidden = false; }
    }
  });
  var sel = raiz.querySelector("[data-nuevo-servicio]");
  if (sel) sel.addEventListener("change", function () {
    if (!sel.value) return;
    var existente = tarjetas.querySelector('[data-card][data-servicio="' + sel.value + '"]');
    var card = existente || crearCard(sel.value, sel.options[sel.selectedIndex].text);
    agregarFila(card); sel.value = "";
  });
  form.addEventListener("submit", function (ev) {
    // Las filas nuevas sin cifras se descartan; a las demás se les quitan los puntos de los miles
    raiz.querySelectorAll("[data-fila]").forEach(function (f) {
      var d = f.querySelector("input[name$=-desde]"), h = f.querySelector("input[name$=-hasta]");
      if (!f.querySelector("input[name$=-id]").value && !d.value && !h.value) f.remove();
    });
    raiz.querySelectorAll("input[name$=-desde], input[name$=-hasta]").forEach(function (i) { i.value = i.value.replace(/\D/g, ""); });
  });
})();
