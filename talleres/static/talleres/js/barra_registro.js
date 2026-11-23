// Barra fija de avance de los registros («Faltan N datos» + Seguir). Compartida por motociclista, taller y mecánico.
// Uso: <form data-barra-form> con el parcial cuentas/_barra_registro.html (data-barra, data-barra-texto, data-barra-relleno,
// data-barra-btn) y un elemento [data-final] (el botón de enviar: al verse, la barra se esconde).
// Por defecto cuenta los campos «required» del formulario; el registro del mecánico pasa su propia lista con TYBarra(form, fn).
(function () {
  function requeridos(form) {
    var vistos = {}, lista = [];
    Array.prototype.slice.call(form.querySelectorAll("input[required], select[required], textarea[required]")).forEach(function (el) {
      if (el.type === "hidden" || el.disabled) return;
      var k = el.type === "radio" ? "r:" + el.name : el.id || el.name;
      if (vistos[k]) return; vistos[k] = 1; lista.push(el);
    });
    return lista;
  }
  function listo(el, form) {
    if (el.type === "checkbox") return el.checked;
    if (el.type === "radio") return !!form.querySelector('input[name="' + el.name + '"]:checked');
    if (el.type === "file") return el.files && el.files.length > 0;
    var v = el.value || "";
    if (/password1$/.test(el.id)) return v.length >= 8 && !/^\d+$/.test(v);
    return v.trim() !== "";
  }
  window.TYBarra = function (form, pendientes) {
    var barra = form.querySelector("[data-barra]"); if (!barra) return;
    var texto = barra.querySelector("[data-barra-texto]"), relleno = barra.querySelector("[data-barra-relleno]"), boton = barra.querySelector("[data-barra-btn]");
    var final = form.querySelector("[data-final]");
    pendientes = pendientes || function () { return requeridos(form).map(function (el) { return [el, listo(el, form)]; }); };
    function revisar() {
      var lista = pendientes(), faltan = lista.filter(function (p) { return !p[1]; }).length;
      texto.textContent = faltan ? (faltan === 1 ? "Falta 1 dato obligatorio" : "Faltan " + faltan + " datos obligatorios") : "Todo listo para enviar";
      relleno.style.width = lista.length ? Math.round(100 * (lista.length - faltan) / lista.length) + "%" : "100%";
      barra.classList.toggle("listo", !faltan);
      boton.textContent = faltan ? "Seguir" : "Enviar";
      barra.dispatchEvent(new CustomEvent("barra:revisada", { detail: lista }));
      return lista;
    }
    barra.hidden = false;
    boton.addEventListener("click", function () {
      var falta = revisar().filter(function (p) { return !p[1]; })[0];
      if (!falta) { if (final) final.scrollIntoView({ behavior: "smooth", block: "center" }); return; }
      barra.dispatchEvent(new CustomEvent("barra:ir", { detail: falta }));
      var el = falta[0];
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      var foco = el.matches("input, select, textarea") ? el : el.querySelector("input:not([type=search])");
      if (foco) setTimeout(function () { foco.focus({ preventScroll: true }); }, 350);
    });
    if (final && "IntersectionObserver" in window) {
      new IntersectionObserver(function (e) { barra.classList.toggle("oculta", e[0].isIntersecting); }).observe(final);
    }
    form.addEventListener("input", revisar); form.addEventListener("change", revisar);
    revisar();
    return revisar;
  };
  document.querySelectorAll("form[data-barra-form]").forEach(function (f) { if (!f.hasAttribute("data-registro-mecanico")) window.TYBarra(f); });
})();
