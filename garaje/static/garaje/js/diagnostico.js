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

  function activar(raiz) {
  raiz.querySelectorAll("[data-guia-pieza]").forEach((b) => {
    b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); abrir(b); });
    // Los números del dibujo son <g role="button">: también se abren con Enter o espacio
    if (b.tagName.toLowerCase() === "g") b.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(b); }
    });
  });

  raiz.querySelectorAll("[data-esquema]").forEach((fig) => {
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
  }
  activar(document);

  // Pestañas (varias causas en láminas distintas): la primera viene abierta; las demás se piden al tocarlas
  function elegirPestana(tab) {
    const seccion = tab.closest("#diag-esquema");
    seccion.querySelectorAll('[role="tab"]').forEach((t) => {
      const activa = t === tab;
      t.classList.toggle("activo", activa);
      t.setAttribute("aria-selected", String(activa));
      t.tabIndex = activa ? 0 : -1;
    });
    seccion.querySelectorAll(".diag-panel").forEach((p) => { p.hidden = p.id !== tab.getAttribute("aria-controls"); });
    const panel = document.getElementById(tab.getAttribute("aria-controls"));
    if (panel.dataset.url && !panel.dataset.cargado) {
      panel.dataset.cargado = "1";
      fetch(panel.dataset.url, { credentials: "same-origin" })
        .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then((html) => { panel.innerHTML = html; activar(panel); })
        .catch(() => {
          delete panel.dataset.cargado;
          panel.querySelector(".diag-cargando-texto").textContent = "No se pudo cargar este dibujo. Toca la pestaña otra vez.";
        });
    }
  }
  document.addEventListener("click", (e) => {
    const tab = e.target.closest('.diag-pestanas [role="tab"]');
    if (tab) elegirPestana(tab);
  });
  document.addEventListener("keydown", (e) => {
    const tab = e.target.closest('.diag-pestanas [role="tab"]');
    if (!tab || !["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const tabs = [...tab.parentElement.children];
    const otra = tabs[(tabs.indexOf(tab) + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    otra.focus();
    elegirPestana(otra);
  });

  // Esquema diferido: llega aparte (los dibujos tardan si no están en caché) y reemplaza el aviso de "cargando"
  const diferido = document.querySelector("#diag-esquema[data-diferido]");
  if (diferido) {
    fetch(diferido.dataset.diferido, { credentials: "same-origin" })
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then((html) => {
        const caja = document.createElement("div");
        caja.innerHTML = html.trim();
        const nuevo = caja.querySelector("#diag-esquema");  // con pestañas, aviso o nada
        if (nuevo) { diferido.replaceWith(nuevo); activar(nuevo); } else diferido.remove();
      })
      .catch(() => {
        diferido.removeAttribute("aria-busy");
        diferido.querySelector(".diag-cargando-texto").textContent = "No se pudo cargar el esquema. Recarga la página para intentarlo de nuevo.";
      });
  }
})();
