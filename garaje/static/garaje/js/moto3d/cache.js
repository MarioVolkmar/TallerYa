// Caché de la carrocería en el navegador (IndexedDB).
import { CALIDAD } from "./comun.js";

// ---------- Caché de la carrocería en el navegador (IndexedDB) ----------
// Los paneles curvos (tanque, carenados, colín…) son lo más lento del armado. La primera visita los calcula y
// los guarda; las siguientes los leen ya listos. Cambiar CACHE_VERSION invalida todo lo guardado.
const CACHE_VERSION = 6;
export const cachePaneles = { firma: "", guardados: {}, nuevos: {}, aciertos: 0 };
function abrirCache() {
  return new Promise((resolver, fallar) => {
    const pedido = indexedDB.open("tallerya-3d", 1);
    pedido.onupgradeneeded = () => pedido.result.createObjectStore("paneles");
    pedido.onsuccess = () => resolver(pedido.result);
    pedido.onerror = () => fallar(pedido.error);
  });
}
export async function prepararCache(datos) {
  cachePaneles.firma = `${CACHE_VERSION}|${CALIDAD.nombre}|${datos.linea || ""}|${JSON.stringify(datos.specs)}`;
  try {
    const db = await abrirCache();
    const leido = await new Promise((resolver) => {
      const pedido = db.transaction("paneles").objectStore("paneles").get(cachePaneles.firma);
      pedido.onsuccess = () => resolver(pedido.result);
      pedido.onerror = () => resolver(null);
    });
    db.close();
    cachePaneles.guardados = leido || {};
  } catch {
    cachePaneles.guardados = {}; // sin IndexedDB (modo privado, bloqueado…): se arma normal
  }
}
export async function guardarCache() {
  if (!Object.keys(cachePaneles.nuevos).length) return;
  try {
    const db = await abrirCache();
    const tx = db.transaction("paneles", "readwrite");
    const t = performance.now();
    tx.objectStore("paneles").put({ ...cachePaneles.guardados, ...cachePaneles.nuevos }, cachePaneles.firma);
    cachePaneles.msGuardar = Math.round(performance.now() - t);
    tx.oncomplete = () => db.close();
  } catch { /* sin caché: no pasa nada */ }
}
