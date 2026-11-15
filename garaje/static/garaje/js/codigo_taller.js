// Código de taller (QR) para que un taller verifique un servicio. Un solo componente para los tres lugares:
// - aviso verde "Aún no está verificado" al elegir un taller de TallerYa (despiece y ventana "Registrar mantenimiento");
// - ventana emergente "Muéstrale esto a <taller>" desde un servicio pendiente de la hoja de vida.
// El servidor (garaje:codigo_taller) reutiliza el código vigente y, si se pasa un registro, lo liga a él.
(function () {
  "use strict";
  const cache = {};

  function cookie(nombre) {
    const m = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`));
    return m ? decodeURIComponent(m[1]) : "";
  }

  async function pedir(url, { nuevo = false, registro = "" } = {}) {
    const previo = cache[url];
    if (!nuevo && !registro && previo && new Date(previo.vence) > Date.now()) return previo;
    const cuerpo = new FormData();
    if (nuevo) cuerpo.append("nuevo", "1");
    if (registro) cuerpo.append("registro", registro);
    const resp = await fetch(url, { method: "POST", body: cuerpo, credentials: "same-origin",
      headers: { "X-Requested-With": "fetch", "X-CSRFToken": cookie("csrftoken") } });
    if (!resp.ok) throw new Error("sin código");
    cache[url] = await resp.json();
    return cache[url];
  }

  // Pinta QR + código + vencimiento en `nodo` (que ya tiene la estructura) y ofrece "Generar otro" al vencer.
  function pintar(nodo, c, url, opciones) {
    nodo.querySelector("[data-qr]").innerHTML = c.qr;
    nodo.querySelector("[data-codigo]").textContent = c.codigo;
    nodo.querySelector("[data-vence]").textContent = `Vence a las ${c.vence_texto}`;
    const otro = nodo.querySelector("[data-otro-codigo]");
    nodo.classList.remove("vencido");
    otro.hidden = true;
    clearTimeout(nodo._reloj);
    nodo._reloj = setTimeout(() => {
      nodo.classList.add("vencido");
      nodo.querySelector("[data-vence]").textContent = "Este código venció.";
      otro.hidden = false;
    }, Math.max(0, new Date(c.vence) - Date.now()));
    otro.onclick = () => cargar(nodo, url, { ...opciones, nuevo: true });
    nodo.dispatchEvent(new CustomEvent("codigo-listo", { detail: c }));
  }

  async function cargar(nodo, url, opciones = {}) {
    try {
      pintar(nodo, await pedir(url, opciones), url, opciones);
    } catch (err) {
      nodo.querySelector("[data-vence]").textContent = "No se pudo traer el código. Ábrelo en tu hoja de vida.";
    }
  }

  const PIEZAS = `
    <div class="codigo-qr" data-qr aria-hidden="true"></div>
    <div class="codigo-texto">
      <strong data-titulo></strong>
      <p data-msg></p>
      <p class="codigo-letras" data-codigo aria-live="polite"></p>
      <small data-vence>Generando código…</small>
      <button type="button" class="codigo-otro" data-otro-codigo hidden>Generar otro</button>
    </div>`;

  // Aviso verde dentro de `cont` (un contenedor vacío con [hidden]): al elegir un taller de TallerYa.
  function aviso(cont, { url, taller }) {
    if (!cont.dataset.armado) {
      cont.classList.add("codigo-aviso");
      cont.innerHTML = PIEZAS;
      cont.querySelector("[data-titulo]").textContent = "Aún no está verificado";
      cont.dataset.armado = "1";
      cont.addEventListener("codigo-listo", (e) => {
        cont.querySelector("[data-msg]").textContent = `Muéstrale este código a ${cont.dataset.taller} `
          + `y quedará verificado en tu hoja de vida (+${e.detail.puntos} pts).`;
      });
    }
    cont.dataset.taller = taller;
    cont.hidden = false;
    cargar(cont, url);
  }

  function ocultar(cont) {
    if (cont) cont.hidden = true;
  }

  // Ventana emergente con el QR grande (hoja de vida → "Mostrar código" de un pendiente).
  let dialogo = null;
  function ventana({ url, registro, taller, servicio }) {
    if (!dialogo) {
      dialogo = document.createElement("dialog");
      dialogo.className = "codigo-dialogo";
      dialogo.setAttribute("aria-labelledby", "codigo-dialogo-titulo");
      dialogo.innerHTML = `<button type="button" class="dialogo-cerrar codigo-cerrar" aria-label="Cerrar">×</button>
        <div class="codigo-ventana">${PIEZAS}</div>`;
      dialogo.querySelector("[data-titulo]").id = "codigo-dialogo-titulo";
      dialogo.querySelector(".codigo-cerrar").addEventListener("click", () => dialogo.close());
      dialogo.addEventListener("click", (e) => { if (e.target === dialogo) dialogo.close(); });
      document.body.appendChild(dialogo);
    }
    const nodo = dialogo.querySelector(".codigo-ventana");
    nodo.querySelector("[data-titulo]").textContent = `Muéstrale esto a ${taller}`;
    nodo.querySelector("[data-msg]").textContent = servicio || "";
    nodo.querySelector("[data-qr]").innerHTML = "";
    nodo.querySelector("[data-codigo]").textContent = "";
    nodo.querySelector("[data-vence]").textContent = "Generando código…";
    dialogo.showModal();
    cargar(nodo, url, { registro });
  }

  // Cableado automático:
  // 1) formularios con [data-codigo-url] y un select de taller: aviso verde en su [data-verificar];
  document.addEventListener("change", (e) => {
    const select = e.target;
    if (!select.matches || !select.matches('select[name="taller"]')) return;
    const form = select.closest("form[data-codigo-url]");
    const cont = form && form.querySelector("[data-verificar]");
    if (!cont) return;
    const deTallerYa = select.value !== "" && select.value !== "otro";
    if (deTallerYa) aviso(cont, { url: form.dataset.codigoUrl, taller: select.selectedOptions[0].textContent });
    else ocultar(cont);
  });
  // 2) "Mostrar código" de un pendiente en la hoja de vida: ventana sin recargar (sin JS, el formulario es el respaldo).
  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form.matches || !form.matches("form[data-codigo-ventana]") || !window.HTMLDialogElement) return;
    e.preventDefault();
    ventana({ url: form.dataset.codigoVentana, registro: form.dataset.registro, taller: form.dataset.taller,
      servicio: form.dataset.servicio });
  });

  window.TallerYaCodigo = { aviso, ocultar, ventana };
})();
