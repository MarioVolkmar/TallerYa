// Minifica el JS del visor 3D para producción (`npm run js`, lo corre build.sh antes de collectstatic).
// Escribe las copias en build_js/ con la misma ruta que en static/ (garaje/js/...): en producción config/settings.py
// pone build_js/ primero en STATICFILES_DIRS, así collectstatic toma la copia minificada. Los originales no se tocan
// y en desarrollo (DEBUG) se siguen sirviendo sin minificar. Los import/export y las rutas de los import quedan iguales.
import fs from "node:fs";
import path from "node:path";
import { minify } from "terser";

const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname).replace(/^\/(\w:)/, "$1"), "..");
const origen = path.join(raiz, "garaje", "static");
const destino = path.join(raiz, "build_js");
const archivos = ["garaje/js/moto3d.js", "garaje/js/moto3d-carga.js",
  ...fs.readdirSync(path.join(origen, "garaje/js/moto3d")).filter((n) => n.endsWith(".js")).map((n) => "garaje/js/moto3d/" + n)];

fs.rmSync(destino, { recursive: true, force: true });
let antes = 0, despues = 0;
for (const rel of archivos) {
  const codigo = fs.readFileSync(path.join(origen, rel), "utf8");
  const esModulo = rel !== "garaje/js/moto3d-carga.js";
  const r = await minify(codigo, { module: esModulo, ecma: 2020, compress: { passes: 2 }, mangle: true, format: { comments: false } });
  fs.mkdirSync(path.dirname(path.join(destino, rel)), { recursive: true });
  fs.writeFileSync(path.join(destino, rel), r.code);
  antes += codigo.length; despues += r.code.length;
}
console.log(`3D minificado: ${archivos.length} archivos, ${Math.round(antes / 1024)} KB → ${Math.round(despues / 1024)} KB (en build_js/)`);
