// Piloto del cotizador de repuestos. Solo se carga con COTIZADOR_ACTIVO=1 (etiqueta {% cotizador_script %}).
// No toca despiece.js: mira la ficha de la pieza y le agrega el botón «Cotizar»; en el plan de mantenimiento usa los
// botones [data-cotizar-codigo]. Pide el recuadro a nuestro servidor (misma origen: la CSP no cambia).
(function () {
  "use strict";
  const yo = document.currentScript;
  const URL_PARTE = yo.dataset.urlParte;   // /cotizador/parte/0/
  const URL_CODIGO = yo.dataset.urlCodigo; // /cotizador/codigo/

  function pedir(url, destino, boton) {
    destino.querySelector(".cotizador-recuadro")?.remove();
    const caja = document.createElement("div");
    caja.className = "cotizador-recuadro cotizador-cargando";
    caja.setAttribute("role", "status");
    caja.textContent = "Buscando precios…";
    destino.appendChild(caja);
    if (boton) boton.disabled = true;
    fetch(url, { credentials: "same-origin", headers: { "X-Requested-With": "fetch" } })
      .then((r) => r.text())
      .then((html) => {
        const plantilla = document.createElement("template");
        plantilla.innerHTML = html.trim(); // HTML de nuestro servidor, ya escapado por Django
        const nuevo = plantilla.content.firstElementChild;
        caja.replaceWith(nuevo || caja);
        nuevo?.querySelector("[data-cotizador-cerrar]")?.addEventListener("click", () => nuevo.remove());
      })
      .catch(() => { caja.textContent = "No pudimos consultar los precios. Revisa tu conexión."; })
      .finally(() => { if (boton) boton.disabled = false; });
  }

  // 1) Ficha de la pieza en el despiece: botón junto a «Ver guía» y «Pedir repuesto».
  const ficha = document.getElementById("parte-ficha");
  if (ficha && URL_PARTE) {
    const idElegida = () => document.querySelector("#partes-lista .parte-fila.elegida, #plano-escena .punto.elegido")?.dataset.id;
    const poner = () => {
      const acciones = ficha.querySelector(".ficha-pieza-acciones");
      if (!acciones || ficha.querySelector(".cotizador-boton")) return;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn-borde text-xs py-3 cotizador-boton cotizador-boton-ficha";
      b.textContent = "Cotizar";
      b.addEventListener("click", () => {
        const id = idElegida();
        if (id) pedir(URL_PARTE.replace("/0/", `/${encodeURIComponent(id)}/`), ficha, b);
      });
      acciones.after(b);
    };
    new MutationObserver(poner).observe(ficha, { childList: true });
    poner();
  }

  // 2) Plan de mantenimiento: «Qué necesitas» → botón Cotizar por repuesto.
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-cotizar-codigo]");
    if (!b || !URL_CODIGO) return;
    const li = b.closest("li");
    if (!li) return;
    let cont = li.nextElementSibling; // el recuadro va en su propia fila, debajo del repuesto
    if (!cont || !cont.classList.contains("cotizador-li")) {
      cont = document.createElement("li");
      cont.className = "cotizador-li";
      li.after(cont);
    }
    pedir(`${URL_CODIGO}?c=${encodeURIComponent(b.dataset.cotizarCodigo)}`, cont, b);
  });
})();
