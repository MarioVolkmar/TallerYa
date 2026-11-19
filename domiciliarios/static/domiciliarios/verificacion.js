// Verificación de TallerYa Ruta: muestra el nombre y una vista previa de la foto elegida (sin subir nada aún).
(function () {
  var form = document.querySelector("[data-dm-verificacion]");
  if (!form) return;
  form.querySelectorAll(".dm-subir input[type=file]").forEach(function (input) {
    input.addEventListener("change", function () {
      var caja = input.closest(".dm-subir");
      var nombre = caja.querySelector("[data-nombre]");
      var archivo = input.files && input.files[0];
      var previa = caja.querySelector("img");
      if (!archivo) { nombre.textContent = "Ninguna elegida"; caja.classList.remove("dm-subir-listo"); if (previa) previa.remove(); return; }
      nombre.textContent = archivo.size >= 5 * 1024 * 1024 ? "Pesa más de 5 MB: elige otra" : "✓ " + archivo.name;
      caja.classList.toggle("dm-subir-listo", archivo.size < 5 * 1024 * 1024);
      if (!previa) { previa = document.createElement("img"); previa.alt = ""; caja.appendChild(previa); }
      previa.src = URL.createObjectURL(archivo);
    });
  });
})();
