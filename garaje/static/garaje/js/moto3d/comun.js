// Utilidades compartidas del visor 3D: calidad según el equipo, medición del armado y pausas para no congelar la página.
import * as THREE from "three";

export const V = (x, y, z = 0) => new THREE.Vector3(x, y, z);
// Tiempos del armado por etapa (ms), para ver en consola con __visor.info().etapas
export const ETAPAS = {};
export function medir(nombre, fn) { const t = performance.now(); const r = fn(); ETAPAS[nombre] = (ETAPAS[nombre] || 0) + performance.now() - t; return r; }

// Calidad según el equipo: en celulares y equipos modestos se usan menos segmentos en curvas y llantas, sombra
// más liviana y menos resolución. A simple vista se ve casi igual y arma y dibuja bastante más rápido.
// Para probar desde la consola: agregar ?calidad=baja o ?calidad=alta a la dirección.
export const CALIDAD = (() => {
  const pedida = new URLSearchParams(location.search).get("calidad");
  const modesto = matchMedia("(pointer: coarse)").matches || (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  const baja = pedida ? pedida === "baja" : modesto;
  return baja
    ? { nombre: "baja", seg: 0.42, subdividir: 0.15, sombra: 512, pixeles: 1.5 }
    : { nombre: "alta", seg: 0.72, subdividir: 0.085, sombra: 1024, pixeles: 1.75 };
})();
export const seg = (n, minimo = 6) => Math.max(minimo, Math.round(n * CALIDAD.seg));


// Pausa corta para que el navegador atienda la página (clics, scroll) entre pedazos del armado.
// scheduler.yield si existe; si no, un mensaje a sí mismo (no lo frena el navegador como a setTimeout).
const canalCeder = new MessageChannel();
const pendientesCeder = [];
canalCeder.port1.onmessage = () => pendientesCeder.shift()?.();
// Pedazo más largo (ms) que el armado tuvo la página ocupada sin soltarla: __visor.info().pedazoMasLargo
export const pedazos = { desde: 0, max: 0 };
// scheduler.yield() pone la continuación delante de las demás tareas: bien para el armado, pero las respuestas de red
// y los clics de la página quedaban en cola hasta que el 3D terminaba (el esquema del despiece esperaba al 3D entero).
// Cada TURNO_MS se cede un turno de verdad, al final de la cola, para que lo demás avance.
const TURNO_MS = 120;
let desdeTurno = 0;
export async function ceder() {
  const ahora = performance.now();
  pedazos.max = Math.max(pedazos.max, ahora - pedazos.desde);
  if (!desdeTurno) desdeTurno = ahora;
  if (window.scheduler?.yield && ahora - desdeTurno < TURNO_MS) await scheduler.yield();
  else {
    await new Promise((r) => { pendientesCeder.push(r); canalCeder.port2.postMessage(0); });
    desdeTurno = performance.now();
  }
  pedazos.desde = performance.now();
}
