// Campanita de notificaciones: abre un panel con las últimas y permite marcarlas como leídas.
(function () {
  const boton = document.getElementById("campana");
  const panel = document.getElementById("campana-panel");
  if (!boton || !panel) return;
  const lista = panel.querySelector(".campana-lista");
  const contador = boton.querySelector(".campana-contador");
  const marcar = panel.querySelector("[data-marcar]");
  const ICONOS = {
    mantenimiento: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9l-3.8 3.8z"/>',
    documento: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    foro: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    taller: '<path d="M3 21V9l9-6 9 6v12"/><path d="M9 21v-6h6v6"/>',
    plus: '<path d="m12 2 2.9 6.3 6.9.7-5.2 4.6 1.5 6.8L12 16.9 5.9 20.4l1.5-6.8L2.2 9l6.9-.7z"/>',
    general: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
  };

  function el(etiqueta, clase, texto) {
    const n = document.createElement(etiqueta);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }
  function cookie(nombre) {
    const m = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`));
    return m ? decodeURIComponent(m[1]) : "";
  }
  function pintarContador(n) {
    contador.textContent = n > 9 ? "9+" : String(n);
    contador.hidden = n === 0;
    boton.setAttribute("aria-label", n ? `Notificaciones: ${n} sin leer` : "Notificaciones");
    marcar.hidden = n === 0;
  }

  async function cargar() {
    lista.innerHTML = '<p class="campana-vacio">Cargando…</p>';
    try {
      const datos = await fetch(panel.dataset.url, { headers: { Accept: "application/json" } }).then((r) => r.json());
      lista.innerHTML = "";
      pintarContador(datos.sin_leer);
      if (!datos.notificaciones.length) {
        lista.appendChild(el("p", "campana-vacio", "Todo tranquilo por aquí. Te avisaremos cuando le toque algo a tu moto."));
        return;
      }
      datos.notificaciones.forEach((n) => {
        const a = el("a", "notif-fila" + (n.leida ? "" : " sin-leer"));
        a.href = n.ir;
        const icono = el("span", `notif-icono notif-${n.tipo}`);
        const relleno = n.tipo === "plus" ? 'fill="currentColor"' : 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';
        icono.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" ${relleno} aria-hidden="true">${ICONOS[n.tipo] || ICONOS.general}</svg>`;
        const textos = el("span", "min-w-0 flex-1");
        textos.append(el("span", "notif-titulo", n.titulo));
        if (n.texto) textos.append(el("span", "notif-texto", n.texto));
        textos.append(el("span", "notif-hace", `hace ${n.hace}`));
        a.append(icono, textos);
        if (!n.leida) a.append(el("span", "notif-punto"));
        lista.appendChild(a);
      });
    } catch (e) {
      lista.innerHTML = '<p class="campana-vacio">No pudimos cargar tus notificaciones.</p>';
    }
  }

  function abrir(si) {
    panel.hidden = !si;
    boton.setAttribute("aria-expanded", String(si));
    if (si) cargar();
  }
  boton.addEventListener("click", (e) => { e.stopPropagation(); abrir(panel.hidden); });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target)) abrir(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) { abrir(false); boton.focus(); } });

  marcar.addEventListener("click", async () => {
    await fetch(marcar.dataset.url, { method: "POST", headers: { "X-Requested-With": "fetch", "X-CSRFToken": cookie("csrftoken") } });
    pintarContador(0);
    lista.querySelectorAll(".sin-leer").forEach((f) => f.classList.remove("sin-leer"));
    lista.querySelectorAll(".notif-punto").forEach((p) => p.remove());
  });
})();
