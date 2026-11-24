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
  const tarjeta = document.querySelector("[data-push-tarjeta]");
  if (!caja && !tarjeta) return;
  const soporta = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  const MSG_LISTO = "Listo: te avisaremos de SOAT, técnico-mecánica, pico y placa, citas y visitas.";
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
  async function actual() {
    const reg = await navigator.serviceWorker.ready;
    return { reg, sub: await reg.pushManager.getSubscription() };
  }
  // Pide el permiso (solo desde un toque de la persona) y registra el celular; devuelve true si quedó activo.
  async function activar(url) {
    const permiso = await Notification.requestPermission();
    if (permiso !== "granted") return false;
    const { reg, sub } = await actual();
    const nueva = sub || await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64(clave) });
    return (await post(url, nueva.toJSON())).ok;
  }
  async function estado(url) {
    const est = await fetch(url, { credentials: "same-origin" }).then((r) => r.json()).catch(() => null);
    if (!est || !est.disponible) return null;
    clave = est.clave;
    const { sub } = await actual();
    activa = !!sub && est.activa;
    return est;
  }

  // Tarjeta discreta (después del registro, en el panel o tras pedir una cita o visita): nunca pide permiso al cargar.
  async function iniciarTarjeta() {
    if (leer("push-tarjeta-no") === "1") return;
    const texto = tarjeta.querySelector("[data-push-texto]");
    const activarBtn = tarjeta.querySelector("[data-push-activar]");
    tarjeta.querySelector("[data-push-descartar]").addEventListener("click", () => { tarjeta.hidden = true; guardar("push-tarjeta-no", "1"); });
    if (!soporta) {
      if (esIOS && !instalada) { // iPhone sin instalar: Safari solo permite avisos desde la app instalada
        texto.textContent = "Instala la app para recibir avisos: toca Compartir y luego «Agregar a inicio».";
        activarBtn.hidden = true; tarjeta.hidden = false;
      }
      return;
    }
    if (Notification.permission === "denied" || !(await estado(tarjeta.dataset.estado)) || activa) return;
    tarjeta.hidden = false;
    activarBtn.addEventListener("click", async () => {
      activarBtn.disabled = true;
      try {
        if (await activar(tarjeta.dataset.suscribir)) {
          texto.textContent = MSG_LISTO; activarBtn.hidden = true;
          tarjeta.querySelector("[data-push-descartar]").textContent = "Cerrar";
        } else texto.textContent = "No se activaron los avisos. Puedes hacerlo luego desde la campanita.";
      } catch (_) { texto.textContent = "No se pudo activar. Intenta de nuevo."; }
      finally { activarBtn.disabled = false; }
    });
  }
  if (tarjeta) iniciarTarjeta();
  if (!caja) return;

  const boton = caja.querySelector("[data-push]");
  const nota = caja.querySelector("[data-push-nota]");
  function pintar() {
    boton.textContent = activa ? "Desactivar avisos en este celular" : "Activar avisos en este celular";
  }
  async function iniciar() {
    if (!soporta) {
      if (esIOS && !instalada) { caja.hidden = false; boton.hidden = true; nota.textContent = "En iPhone, instala TallerYa (Compartir → Agregar a inicio) para recibir avisos."; }
      return;
    }
    if (!(await estado(caja.dataset.estado))) return;
    if (Notification.permission === "denied") { caja.hidden = false; boton.hidden = true; nota.textContent = "Bloqueaste los avisos en el navegador; actívalos desde los ajustes del sitio."; return; }
    caja.hidden = false; pintar();
  }
  boton.addEventListener("click", async () => {
    boton.disabled = true;
    try {
      if (activa) {
        const { sub } = await actual();
        if (sub) { await post(caja.dataset.desactivar, { endpoint: sub.endpoint }); await sub.unsubscribe(); }
        activa = false; nota.textContent = "";
      } else {
        const ok = await activar(caja.dataset.suscribir);
        activa = ok; nota.textContent = ok ? MSG_LISTO : "No se activaron los avisos.";
      }
      pintar();
    } catch (_) { nota.textContent = "No se pudo cambiar el aviso. Intenta de nuevo."; }
    finally { boton.disabled = false; }
  });
  iniciar();
})();
