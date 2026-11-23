/* «Multimarca»: al elegirla se apagan las marcas sueltas (no se envían) y queda solo la bandera */
(function () {
  document.querySelectorAll("[data-marcas]").forEach(function (caja) {
    var multi = caja.querySelector("input[name=multimarca]"); if (!multi) return;
    var otras = Array.prototype.filter.call(caja.querySelectorAll("input[type=checkbox]"), function (i) { return i !== multi; });
    function aplicar(limpiar) {
      otras.forEach(function (i) { if (multi.checked && limpiar) i.checked = false; i.disabled = multi.checked; });
    }
    multi.addEventListener("change", function () { aplicar(true); });
    aplicar(false);
  });
})();
