// Métricas de uso propias (sin terceros ni cookies nuevas). Las páginas encolan eventos sin esperar a este archivo:
//   (window.tyM = window.tyM || []).push(["visor_3d", {origen: "moto"}]);
(function () {
  var cola = window.tyM || [];
  var nav = navigator;
  if (nav.doNotTrack === "1" || nav.globalPrivacyControl) { window.tyM = { push: function () {} }; return; }
  function csrf() {
    var m = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    if (m) return decodeURIComponent(m[1]);
    var i = document.querySelector("input[name=csrfmiddlewaretoken]");
    return i ? i.value : "";
  }
  var vistos = {};
  function enviar(e) {
    var nombre = e[0], datos = e[1] || {};
    var llave = nombre + JSON.stringify(datos);
    if (vistos[llave]) return; // la misma pieza tocada dos veces en la visita cuenta una
    vistos[llave] = 1;
    try {
      fetch("/metricas/evento/", {
        method: "POST", credentials: "same-origin", keepalive: true,
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({ nombre: nombre, datos: datos })
      }).catch(function () {});
    } catch (err) {}
  }
  window.tyM = { push: enviar };
  cola.forEach(enviar);
})();
