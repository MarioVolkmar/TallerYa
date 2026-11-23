/* Registrar servicio (taller): placa con formato y consulta en vivo, chips del plan, km y $ con puntos de miles. */
(function () {
  var f = document.getElementById("sr");
  if (!f) return;
  var placa = document.getElementById("sr-placa"), codigo = document.getElementById("sr-codigo");
  var km = f.querySelector('[name="km"]'), costo = f.querySelector('[name="costo"]');
  var aviso = document.getElementById("sr-moto"), srv = document.getElementById("sr-moto-srv");
  var chips = document.getElementById("sr-chips"), sinplan = document.getElementById("sr-sinplan");
  var kmAviso = document.getElementById("sr-km-aviso"), despues = document.getElementById("sr-despues");
  var enviar = document.getElementById("sr-enviar");
  var kmActual = srv ? parseInt((srv.textContent.match(/([\d.]+) km/) || [0, "0"])[1].replace(/\./g, ""), 10) : null;
  var ultima = "", temporizador = null, pedido = 0;

  function miles(txt) {
    var d = String(txt).replace(/\D/g, "");
    return d ? d.replace(/\B(?=(\d{3})+(?!\d))/g, ".") : "";
  }
  function num(txt) { return parseInt(String(txt).replace(/\D/g, ""), 10) || 0; }
  function limpiar(el, fn) { el.addEventListener("input", function () { el.value = fn(el.value); }); }

  function mostrar(clase, html) {
    if (srv) srv.hidden = true;
    aviso.className = "sr-moto " + clase;
    aviso.innerHTML = html;
    aviso.hidden = !html;
  }
  function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

  function pintarChips(tareas) {
    var marcadas = {};
    Array.prototype.forEach.call(chips.querySelectorAll("input:checked"), function (i) { marcadas[i.value] = 1; });
    chips.innerHTML = "";
    tareas.forEach(function (t) {
      var l = document.createElement("label"), i = document.createElement("input"), s = document.createElement("span");
      l.className = "sr-chip"; i.type = "checkbox"; i.name = "tareas"; i.value = t.id; i.checked = !!marcadas[t.id];
      s.textContent = t.nombre; l.appendChild(i); l.appendChild(s); chips.appendChild(l);
    });
    sinplan.hidden = tareas.length > 0;
    if (!tareas.length) sinplan.textContent = "Esta moto aún no tiene plan: escribe abajo qué se le hizo.";
  }

  function avisoKm() {
    if (kmActual == null || !km.value) { kmAviso.hidden = true; return; }
    var n = num(km.value);
    if (n < kmActual) {
      kmAviso.textContent = "Es menor que el último registrado (" + miles(kmActual) + " km). Revísalo.";
      kmAviso.hidden = false;
    } else { kmAviso.hidden = true; }
  }

  function consultar() {
    var p = placa.value;
    if (p.length < 5 || p === ultima) return;
    ultima = p;
    var mio = ++pedido;
    mostrar("sr-moto-wait", "Buscando la moto…");
    fetch(f.dataset.url + "?placa=" + encodeURIComponent(p), { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (mio !== pedido) return;
        if (d.estado === "ok") {
          kmActual = d.km;
          mostrar("sr-moto-ok", "<strong>" + esc(d.moto) + "</strong><small>Última lectura: " + miles(d.km) + " km · el dueño está en TallerYa</small>");
          pintarChips(d.tareas);
          avisoKm();
        } else if (d.estado === "no_esta") {
          kmActual = null; pintarChips([]);
          sinplan.hidden = false; sinplan.textContent = "Escribe la placa y salen los trabajos del plan de esa moto.";
          mostrar("sr-moto-no", "Esa placa no está en TallerYa. Pídele al dueño que registre su moto (es gratis) o usa su código.");
        } else if (d.estado === "tope") {
          mostrar("sr-moto-no", "Muchas consultas seguidas. Puedes registrar igual: se valida al enviar.");
        } else { mostrar("", ""); }
      })
      .catch(function () { if (mio === pedido) mostrar("", ""); });
  }

  limpiar(placa, function (v) { return v.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8); });
  placa.addEventListener("input", function () {
    ultima = ""; clearTimeout(temporizador);
    if (placa.value.length < 5) { pedido++; mostrar("", ""); kmActual = null; kmAviso.hidden = true; return; }
    temporizador = setTimeout(consultar, 350);
  });
  if (codigo) {
    limpiar(codigo, function (v) { return v.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12); });
    var porCodigo = function () {
      var con = codigo.value.length > 0;
      enviar.textContent = con ? "Registrar y verificar" : "Registrar servicio";
      despues.textContent = con ? "Queda verificado de una vez en la hoja de vida y le pedimos al dueño que te califique."
                                : "Le avisamos al dueño para que confirme y te califique.";
    };
    codigo.addEventListener("input", porCodigo); porCodigo();
  }
  km.value = miles(km.value); costo.value = miles(costo.value);
  limpiar(km, miles); limpiar(costo, miles);
  km.addEventListener("input", avisoKm);
  if (placa.value.length >= 5 && !srv) consultar();
  avisoKm();
})();
