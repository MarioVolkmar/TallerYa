// Registro de mecánico a domicilio por pasos (uno a la vez en pantalla). Sin JS se ven todos los pasos seguidos
// y el formulario funciona igual: el servidor valida todo al enviar.
(function () {
  var form = document.getElementById("dom-registro");
  if (!form) return;
  var pasos = Array.prototype.slice.call(form.querySelectorAll(".dom-paso"));
  var marcas = document.querySelectorAll("[data-ir-paso]");
  var actual = 0;

  function mostrar(i, enfocar) {
    actual = Math.max(0, Math.min(i, pasos.length - 1));
    pasos.forEach(function (p, j) { p.hidden = j !== actual; });
    marcas.forEach(function (m, j) {
      m.classList.toggle("hecho", j < actual);
      m.classList.toggle("actual", j === actual);
      if (j === actual) m.setAttribute("aria-current", "step"); else m.removeAttribute("aria-current");
    });
    if (enfocar) {
      form.parentElement.scrollIntoView({ behavior: "smooth", block: "start" });
      var primero = pasos[actual].querySelector("input:not([type=hidden]), select, textarea");
      if (primero) primero.focus({ preventScroll: true });
    }
  }

  function pasoValido(paso) {
    // Campos obligatorios del paso (el navegador muestra su aviso) y grupos de casillas marcados como obligatorios
    var campos = paso.querySelectorAll("input[required], select[required], textarea[required]");
    for (var i = 0; i < campos.length; i++) {
      if (!campos[i].checkValidity()) { campos[i].reportValidity(); return false; }
    }
    var grupos = paso.querySelectorAll("[data-requerido]");
    for (var k = 0; k < grupos.length; k++) {
      if (!grupos[k].querySelector("input:checked")) {
        grupos[k].classList.add("dom-grupo-falta");
        grupos[k].scrollIntoView({ behavior: "smooth", block: "center" });
        return false;
      }
      grupos[k].classList.remove("dom-grupo-falta");
    }
    return true;
  }

  form.addEventListener("click", function (e) {
    if (e.target.closest("[data-siguiente]")) {
      if (pasoValido(pasos[actual])) mostrar(actual + 1, true);
    } else if (e.target.closest("[data-atras]")) {
      mostrar(actual - 1, true);
    }
  });
  form.addEventListener("change", function (e) {
    var grupo = e.target.closest("[data-requerido]");
    if (grupo && grupo.querySelector("input:checked")) grupo.classList.remove("dom-grupo-falta");
  });

  // Si el servidor devolvió errores, abrir el primer paso que los tenga
  var conError = pasos.findIndex(function (p) { return p.querySelector(".error"); });
  mostrar(conError >= 0 ? conError : 0, false);
})();
