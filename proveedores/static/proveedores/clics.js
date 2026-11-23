// Cuenta los clics a WhatsApp y a llamar de los proveedores (grúas, CDA…): un POST sin cuerpo a data-clic.
// No envía nada del motero (ni ubicación ni cookies propias): el servidor solo suma 1 al contador del día.
document.addEventListener("click", function (e) {
  var a = e.target.closest && e.target.closest("a[data-clic]");
  if (a && navigator.sendBeacon) navigator.sendBeacon(a.getAttribute("data-clic"));
});
