// App instalable (PWA): service worker, botón "Instala TallerYa" y avisos push.
(function () {
  const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch (_) {} };
  const leer = (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } };
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || "";
  const instalada = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone;

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {}));
  }

  // --- Instalar ---
  const barra = document.getElementById("instalar-app");
  let evento = null;
  const DIAS14 = 14 * 24 * 3600 * 1000;
  const ocultaHasta = () => Number(leer("instalar-oculto-hasta")) || 0;
  const entradas = document.querySelectorAll("[data-instalar-app]");
  function mostrarEntradas() { if (!instalada) entradas.forEach((n) => { n.hidden = false; }); }
  function pintarBarra(ios) {
    if (!barra) return;
    barra.hidden = false;
    barra.querySelectorAll("[data-ios]").forEach((n) => { n.hidden = !ios; });
    barra.querySelectorAll("[data-android]").forEach((n) => { n.hidden = ios; });
  }
  function mostrarBarra(ios) {
    mostrarEntradas();
    if (!barra || instalada || Date.now() < ocultaHasta()) return;
    pintarBarra(ios);
  }
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); evento = e; mostrarBarra(false); });
  window.addEventListener("appinstalled", () => { if (barra) barra.hidden = true; });
  const esIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
  if (esIOS) mostrarBarra(true);
  if (barra) {
    barra.querySelector("[data-instalar]").addEventListener("click", async () => {
      if (!evento) return;
      evento.prompt();
      await evento.userChoice.catch(() => {});
      evento = null; barra.hidden = true;
    });
    barra.querySelector("[data-cerrar]").addEventListener("click", () => { barra.hidden = true; guardar("instalar-oculto-hasta", String(Date.now() + DIAS14)); });
  }
  // Entrada fija "Instalar app" (menú y Mi cuenta): siempre disponible aunque se haya cerrado la barra.
  entradas.forEach((n) => n.addEventListener("click", async (ev) => {
    ev.preventDefault();
    if (evento) { evento.prompt(); await evento.userChoice.catch(() => {}); evento = null; entradas.forEach((x) => { x.hidden = true; }); }
    else if (esIOS) pintarBarra(true);
  }));

  // --- Push ---
  const caja = document.getElementById("push-caja");
  if (!caja) return;
  const boton = caja.querySelector("[data-push]");
  const nota = caja.querySelector("[data-push-nota]");
  const soporta = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  let clave = "", activa = false;

  const b64 = (s) => {
    const p = "=".repeat((4 - (s.length % 4)) % 4);
    const r = atob((s + p).replace(/-/g, "+").replace(/_/g, "/"));
    return Uint8Array.from(r, (c) => c.charCodeAt(0));
  };
  const post = (url, cuerpo) => fetch(url, {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() }, body: JSON.stringify(cuerpo),
  });
  function pintar() {
    boton.textContent = activa ? "Desactivar avisos en este celular" : "Activar avisos en este celular";
  }
  async function actual() {
    const reg = await navigator.serviceWorker.ready;
    return { reg, sub: await reg.pushManager.getSubscription() };
  }
  async function iniciar() {
    if (!soporta) {
      if (esIOS && !instalada) { caja.hidden = false; boton.hidden = true; nota.textContent = "En iPhone, instala TallerYa (Compartir → Agregar a inicio) para recibir avisos."; }
      return;
    }
    const est = await fetch(caja.dataset.estado, { credentials: "same-origin" }).then((r) => r.json()).catch(() => null);
    if (!est || !est.disponible) return;
    clave = est.clave;
    const { sub } = await actual();
    activa = !!sub && est.activa;
    if (Notification.permission === "denied") { caja.hidden = false; boton.hidden = true; nota.textContent = "Bloqueaste los avisos en el navegador; actívalos desde los ajustes del sitio."; return; }
    caja.hidden = false; pintar();
  }
  boton.addEventListener("click", async () => {
    boton.disabled = true;
    try {
      const { reg, sub } = await actual();
      if (activa) {
        if (sub) { await post(caja.dataset.desactivar, { endpoint: sub.endpoint }); await sub.unsubscribe(); }
        activa = false; nota.textContent = "";
      } else {
        const permiso = await Notification.requestPermission();
        if (permiso !== "granted") { nota.textContent = "No se activaron los avisos."; return; }
        const nueva = sub || await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64(clave) });
        const r = await post(caja.dataset.suscribir, nueva.toJSON());
        activa = r.ok; nota.textContent = r.ok ? "Listo: te avisaremos de SOAT, técnico-mecánica, pico y placa y mantenimiento." : "No se pudo activar.";
      }
      pintar();
    } catch (_) { nota.textContent = "No se pudo cambiar el aviso. Intenta de nuevo."; }
    finally { boton.disabled = false; }
  });
  iniciar();
})();
