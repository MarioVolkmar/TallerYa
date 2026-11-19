// Mi ruta: montos rápidos del cierre de jornada (un toque llena "¿Cuánto ganaste hoy?").
(function () {
  var form = document.querySelector("[data-dm-jornada]");
  if (!form) return;
  var campo = form.querySelector("input[name=ingreso]");
  form.querySelectorAll("[data-monto]").forEach(function (b) {
    b.addEventListener("click", function () {
      campo.value = b.getAttribute("data-monto");
      form.querySelectorAll("[data-monto]").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      campo.focus();
    });
  });
})();
