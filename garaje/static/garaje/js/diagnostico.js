// Diagnóstico guiado: el esquema del sistema abre la guía de pieza del despiece (despiece.js) como ventana
// emergente, sin salir de /diagnostico/. Lista y dibujo se resaltan entre sí.
(function () {
  // El visor del despiece va montado fuera de pantalla solo para su guía: lo demás no debe recibir el foco
  document.querySelectorAll(".diag-despiece-fuera .despiece-sistemas, .diag-despiece-fuera .despiece-panel, " +
    ".diag-despiece-fuera .visor-barra, .diag-despiece-fuera .plano, .diag-despiece-fuera .plano-ayuda")
    .forEach((e) => { e.inert = true; });

  function abrir(b) {
    const despiece = window.TallerYaDespiece;
    if (!despiece || !despiece.abrirGuia) return;
    despiece.abrirGuia(Number(b.dataset.guiaPieza), { sospechosa: b.classList.contains("cand") });
  }

  document.querySelectorAll("[data-guia-pieza]").forEach((b) => {
    b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); abrir(b); });
    // Los números del dibujo son <g role="button">: también se abren con Enter o espacio
    if (b.tagName.toLowerCase() === "g") b.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(b); }
    });
  });

  document.querySelectorAll("[data-esquema]").forEach((fig) => {
    const marcar = (id) => {
      fig.querySelectorAll(".activa").forEach((e) => e.classList.remove("activa"));
      if (id) fig.querySelectorAll(`[data-id="${id}"]`).forEach((e) => e.classList.add("activa"));
    };
    fig.querySelectorAll(".diag-esq-lista button, .dg-num").forEach((e) => {
      e.addEventListener("pointerenter", () => marcar(e.dataset.id));
      e.addEventListener("focus", () => marcar(e.dataset.id));
    });
    fig.addEventListener("pointerleave", () => marcar(null));
  });
})();
