// Registro de mecánico a domicilio y servicio a domicilio del taller (mi_taller.html): selector de zonas, «ver más» servicios, WhatsApp y tarifa con formato,
// validación al salir de cada campo y barra fija con el avance. Sin JS el formulario funciona igual (casillas reales).
(function () {
  var form = document.querySelector("[data-registro-mecanico], [data-servicio-taller]"); if (!form) return;
  var $ = function (s, r) { return (r || form).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || form).querySelectorAll(s)); };

  // ---- Zonas: atajos, buscador, «Todas» por grupo y cuenta de elegidas
  var zonas = $("[data-zonas]"), buscar = $("[data-zonas-buscar]"), cuenta = $("[data-zonas-cuenta]");
  var chipsZona = $$("[data-zonas-panel] input[type=checkbox]");
  function modo() { var r = $("input[name=zona_modo]:checked"); return r ? r.value : ""; }
  function contarZonas() {
    var n = chipsZona.filter(function (c) { return c.checked; }).length;
    if (cuenta) cuenta.textContent = n ? (n === 1 ? "1 elegida" : n + " elegidas") : "Comunas o municipios";
    return n;
  }
  buscar.hidden = false;
  buscar.addEventListener("input", function () {
    var q = buscar.value.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim(), hay = false;
    $$("[data-grupo]").forEach(function (g) {
      var visibles = 0;
      $$("[data-chip]", g).forEach(function (chip) {
        var t = chip.textContent.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
        chip.hidden = q && t.indexOf(q) < 0; if (!chip.hidden) visibles++;
      });
      g.hidden = !visibles; if (visibles) hay = true;
    });
    $("[data-zonas-nada]").hidden = hay;
  });
  $$("[data-todas]").forEach(function (b) {
    b.hidden = false;
    b.addEventListener("click", function () {
      var cajas = $$("input[type=checkbox]", b.closest("[data-grupo]"));
      var todas = cajas.every(function (c) { return c.checked; });
      cajas.forEach(function (c) { c.checked = !todas; });
      contarZonas(); revisarTodo();
    });
  });
  zonas.addEventListener("change", function () { contarZonas(); limpiarError(zonas); revisarTodo(); });
  // Sin atajo elegido pero con zonas marcadas (p. ej. al volver con errores): queda en «Elegir zonas»
  if (!modo() && contarZonas()) { var e = $("input[name=zona_modo][value=elegir]"); if (e) e.checked = true; }
  contarZonas();

  // ---- Servicios: los 6 más comunes a la vista y «+ N más» (los marcados siempre se ven)
  var extras = $$(".rm-extra"), mas = $("[data-ver-mas]");
  var ocultas = extras.filter(function (l) { return !l.querySelector("input").checked; });
  if (ocultas.length) {
    ocultas.forEach(function (l) { l.hidden = true; });
    mas.hidden = false; mas.textContent = "+ " + ocultas.length + " más";
    mas.addEventListener("click", function () { ocultas.forEach(function (l) { l.hidden = false; }); mas.remove(); });
  }
  $("[data-servicios]").addEventListener("change", function () { limpiarError($("[data-servicios]")); revisarTodo(); });

  // ---- Formato en vivo: WhatsApp «300 123 4567» y tarifa «25.000»
  var wa = $("#id_whatsapp"), tarifa = $("#id_tarifa_visita");
  function digitos(v) { return (v || "").replace(/\D/g, ""); }
  function formatoWa(v) {
    var d = digitos(v); if (d.length === 12 && d.indexOf("57") === 0) d = d.slice(2);
    d = d.slice(0, 10);
    return d.length > 6 ? d.slice(0, 3) + " " + d.slice(3, 6) + " " + d.slice(6) : d.length > 3 ? d.slice(0, 3) + " " + d.slice(3) : d;
  }
  function miles(v) { var d = digitos(v).replace(/^0+(?=\d)/, "").slice(0, 7); return d.replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  if (wa) { wa.value = formatoWa(wa.value); wa.addEventListener("input", function () { wa.value = formatoWa(wa.value); }); }
  if (tarifa) { tarifa.value = miles(tarifa.value); tarifa.addEventListener("input", function () { tarifa.value = miles(tarifa.value); }); }

  // ---- Validación al salir de cada campo (mensajes cortos; el servidor valida igual)
  var reglas = {
    "id_cuenta-email": function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "" : "Escribe un correo válido."; },
    "id_cuenta-password2": function (v) { var p = $("#id_cuenta-password1"); return p && v === p.value ? "" : "Las contraseñas no coinciden."; },
    "id_nombre": function (v) { return v.trim().length >= 3 ? "" : "Escribe tu nombre (mínimo 3 letras)."; },
    "id_whatsapp": function (v) { var d = digitos(v); return d.length === 10 && d[0] === "3" ? "" : "Debe tener 10 dígitos y empezar por 3."; },
    "id_cedula": function (v) { var d = digitos(v); return d.length >= 5 && d.length <= 11 ? "" : "Escribe solo el número (5 a 11 dígitos)."; }
  };
  function caja(el) { return el.closest(".rc-campo") || el; }
  function limpiarError(c) { var a = c.querySelector(".error-vivo"); if (a) a.remove(); c.classList.toggle("con-error", !!c.querySelector(".error")); }
  function ponerError(c, texto) {
    var a = c.querySelector(".error-vivo") || c.querySelector(".error");
    if (!a) { a = document.createElement("p"); a.className = "error error-vivo"; c.appendChild(a); }
    a.textContent = texto; c.classList.add("con-error");
    var ayuda = c.querySelector(".rc-ayuda"); if (ayuda) ayuda.hidden = true;
  }
  function valida(id, mostrar) {
    var el = document.getElementById(id); if (!el) return true;
    var msj = el.value.trim() ? reglas[id](el.value) : "Este dato es obligatorio.";
    if (mostrar) { if (msj) ponerError(caja(el), msj); else { limpiarError(caja(el)); var a = caja(el).querySelector(".rc-ayuda"); if (a) a.hidden = false; } }
    return !msj;
  }
  Object.keys(reglas).forEach(function (id) {
    var el = document.getElementById(id); if (!el) return;
    el.addEventListener("blur", function () { if (el.value.trim()) valida(id, true); });
    el.addEventListener("input", function () { if (caja(el).querySelector(".error")) valida(id, true); revisarTodo(); });
  });

  // ---- Lo obligatorio, en orden: [elemento al que llevar, nombre corto, ¿listo?]
  function pendientes() {
    var lista = [];
    ["id_cuenta-email", "id_cuenta-password1", "id_cuenta-password2", "id_nombre", "id_whatsapp"].forEach(function (id) {
      var el = document.getElementById(id); if (!el) return;
      var ok = id === "id_cuenta-password1" ? el.value.length >= 8 && !/^\d+$/.test(el.value) : valida(id, false);
      lista.push([el, ok]);
    });
    var m = modo();
    lista.push([zonas, m === "medellin" || m === "valle" || (m === "elegir" && contarZonas() > 0) || (!m && contarZonas() > 0), "zonas"]);
    lista.push([$("[data-servicios]"), $$("[data-servicios] input:checked").length > 0, "servicios"]);
    var ced = document.getElementById("id_cedula"); if (ced && ced.required) lista.push([ced, valida("id_cedula", false)]);
    return lista;
  }

  // ---- Barra fija compartida (talleres/js/barra_registro.js): «Faltan N datos» + Seguir (lleva al primero que falta)
  var barra = $("[data-barra]"), revisarBarra = null;
  function revisarTodo() { return revisarBarra ? revisarBarra() : []; }
  if (!barra || !window.TYBarra) return;  // mi_taller: sin barra de avance
  barra.addEventListener("barra:ir", function (e) {
    var falta = e.detail, el = falta[0];
    if (falta[2] === "zonas") ponerError(zonas, "Elige dónde atiendes.");
    else if (falta[2] === "servicios") ponerError($("[data-servicios]"), "Elige al menos un trabajo.");
    else if (el.id && reglas[el.id]) valida(el.id, true);
  });
  barra.addEventListener("barra:revisada", function (e) {
    $$("[data-seccion]").forEach(function (sec) {
      var listo = e.detail.every(function (p) { return p[1] || !sec.contains(p[0]); });
      sec.querySelector("[data-hecho]").hidden = !listo;
    });
  });
  revisarBarra = window.TYBarra(form, pendientes);
})();
