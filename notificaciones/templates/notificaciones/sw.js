// Service worker de TallerYa: caché de estáticos, página sin conexión y avisos push.
const VERSION = "tallerya-{{ version }}";
const OFFLINE = "{{ offline_url }}";
const ICONO = "{{ icono }}";
const INSIGNIA = "{{ insignia }}";

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.add(OFFLINE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // Estáticos propios: primero la red (siempre al día) y la caché solo si no hay conexión.
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(
      fetch(req).then((r) => { if (r.ok) { const c = r.clone(); caches.open(VERSION).then((ca) => ca.put(req, c)); } return r; })
        .catch(() => caches.match(req))
    );
    return;
  }
  // Páginas: siempre de la red; "Sin conexión" solo si falla 3 veces seguidas (un reinicio corto del servidor no cuenta).
  if (req.mode === "navigate") {
    e.respondWith((async () => {
      for (let i = 0; i < 3; i++) {
        try { return await fetch(req); } catch (_) { await new Promise((r) => setTimeout(r, 1200)); }
      }
      return (await caches.match(OFFLINE)) || Response.error();
    })());
  }
});

self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { titulo: "TallerYa", texto: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.titulo || "TallerYa", {
    body: d.texto || "", icon: ICONO, badge: INSIGNIA, tag: d.tag || "tallerya", data: { url: d.url || "/" },
  }));
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const destino = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((ws) => {
    for (const w of ws) { if ("focus" in w) { w.navigate(destino); return w.focus(); } }
    return self.clients.openWindow(destino);
  }));
});
