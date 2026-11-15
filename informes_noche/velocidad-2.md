# Velocidad 2: tiempos de carga (15-nov-2026)

Sin commit. Suite completa: 526 pruebas OK. Nada cambia a la vista (el CSS minificado da en Chrome las mismas reglas que el original, comprobado regla a regla).

## Archivos tocados
- `talleres/estaticos.py` (nuevo): `EstaticosComprimidos` = el almacén de WhiteNoise (hash, caché inmutable, .gz/.br) que además
  **minifica el CSS propio** al correr `collectstatic` (sin comentarios ni espacios sobrantes; no toca comillas, `calc()`, comas
  ni selectores; tampoco el admin ni los `.min.css`). En local (DEBUG) no se usa.
- `config/settings.py`: STORAGES de producción → `talleres.estaticos.EstaticosComprimidos` (una línea).
- `requirements.txt`: `Brotli>=1.1` → WhiteNoise crea también los `.br`. **No lo pude instalar en local** (instalar paquetes
  quedó bloqueado por permisos): se instalará en el build de Render; si faltara, WhiteNoise sigue con .gz sin fallar.
- `config/urls.py`: `/media/` con `Cache-Control: public, max-age=7 días` (cada subida tiene nombre propio: uuid o sufijo de Django).
- `notificaciones/views.py`: el manifiesto PWA con caché de 1 hora (el navegador lo pedía en cada página).
- `talleres/tests_estaticos.py` (nuevo, 7 pruebas).

## Cómo se midió
- Servidor: cliente de pruebas (`HTTP_HOST=localhost`), mejor de 3, `CaptureQueriesContext`. Los ms varían ±50 % (la máquina
  tenía otras sesiones trabajando); las consultas son exactas.
- Navegador: Chrome sin cabeza por CDP (FCP/LCP de la Performance API). "Antes" en el servidor de desarrollo `tallerya` (8001).
  "Después": servidor local **en modo producción** (DEBUG=0, WhiteNoise con hash y .gz) con el almacén original (8011) y el
  nuevo (8012), con red simulada 4G rápida (9 Mbps, 60 ms) o 4G lenta (1,6 Mbps, 150 ms) y perfil nuevo en cada carga.
- El 3D en Chrome sin cabeza usa GPU por software (SwiftShader): sus tiempos de compilación son peores que en un equipo real;
  sirven para comparar, no como valor absoluto.

## Tabla "antes" (desarrollo, 8001)
| Página | Servidor ms | SQL | HTML KB (gzip) | CSS KB | JS (n / KB) | Bloqueantes | FCP frío / caliente ms |
|---|---|---|---|---|---|---|---|
| Portada anónimo | 115 | 14 | 99 (20) | 464 | 5 / 32 | 2 CSS | 1764 / 1408 |
| Portada con sesión | 145 | 20 | 59 (12) | 460 | 5 / 32 | 2 CSS | 1044 / 928 |
| Mi garaje | 88 | 10 | 37 (7) | 460 | 4 / 31 | 2 CSS | 360 / 296 |
| Moto (3D) | 78–288 | 30 | 169 (27) | 460 | 9 / 135 (+three.js) | 2 CSS + `moto3d-carga.js` | 936 / 772 |
| Diagnóstico | 43 | 6 | 28 (6) | 460 | 5 / 36 | 2 CSS | 364 / 284 |
| Despiece JSON (moto) | 21 (220 la 1.ª) | 12 | 308 (36) | – | – | – | – |
| Talleres | 121 | 11 | 57 (9) | 469 | 5 / 32 | 2 CSS | 520 / 444 |
| Detalle de taller | 71 | 9 | 36 (8) | 469 | 5 / 32 | 2 CSS | 320 / 284 |
| Foro | 80 | 5 | 74 (14) | 460 | 4 / 31 | 2 CSS | 268 / 188 |
| Pregunta (31 resp.) | 64–131 | 9 | 125 (12) | 460 | 5 / 46 | 2 CSS | 384 / 288 |
| Rodada | 68 | 15 | 35 (8) | 460 | 5 / 46 | 2 CSS | 236 / – |
| Técnico-mecánica | 61 | 11 | 34 (7) | 460 | 4 / 31 | 2 CSS | 248* |
\* la carga fría de técnico-mecánica (2824 ms) coincidió con un pico de la máquina; en caliente, 248 ms.

Hallazgos:
- **El servidor no es el cuello**: el SQL suma <1 ms por página (SQLite) y ninguna página tiene N+1 (la tanda anterior ya lo
  arregló; `foro/tests_velocidad.py` y `garaje/tests_velocidad.py` lo vigilan). El tiempo es de plantillas: ficha de la moto
  ~78 ms sin ruido (`_tarea.html` ×14 ≈ 13 ms, base ≈ 12 ms); pregunta larga ~64 ms (≈2 ms por respuesta en 6 `include`).
  En Postgres cada consulta suma ~0,5–1 ms de red: la ficha (30) es la única que se nota (~20–30 ms). Conexión persistente ya
  activa (`conn_max_age=600`).
- **Lo que más pesa en todas las páginas es `tallerya.css`**: 440 KB, bloquea el pintado, 82 KB con gzip. Cobertura medida
  en 15 páginas (escritorio y celular): solo ~147 KB de reglas se usan; ~36 KB son reglas cuyas clases no aparecen en ninguna
  plantilla, JS ni Python (muertas casi seguro; prefijos `diag-`, `tr-`, `fo-`, `agenda-`, `portada-`…); el resto es CSS de
  otras páginas.
- Imágenes: pocas y pequeñas; las de abajo ya tienen `loading="lazy"`. Fuentes: ya con `preconnect` + carga no bloqueante.
  Todos los JS de la base van con `defer`. Estáticos en producción: hash + `max-age=10 años, immutable` (WhiteNoise).

## Tabla "después" (modo producción local)
| Recurso / página | Almacén original | Nuevo | Cambio |
|---|---|---|---|
| `tallerya.css` en disco | 440 KB | 377 KB | −14 % |
| `tallerya.css` transferido (gzip) | 84,9 KB | 66,3 KB | −22 % |
| `tallerya.css` con Brotli (Render) | – | ≈55 KB (estimado) | ≈−35 % |
| Todo el CSS propio (7 hojas, gzip) | 95 KB | 76 KB | −20 % |
| Foro, FCP frío, 4G lenta (mediana de 5) | 1640 ms | 1576 ms | −64 ms |
| Foro, LCP frío, 4G lenta (mediana de 5) | 3060 ms | 2848 ms | ≈−200 ms (con ruido) |
| `/media/` (fotos de talleres, avatares) | sin caché | 7 días | 2.ª visita sin descargas |
| Manifiesto PWA | sin caché | 1 hora | una petición menos por página |
Servidor y SQL: sin cambios (no había nada que ganar sin reorganizar vistas). En 4G rápida la diferencia del CSS (~18 KB)
se pierde en el ruido; en la visita repetida el CSS sale de caché (inmutable) igual que antes.

## 3D y despiece (no tocados; para la sesión experta)
Ficha de la moto en modo producción, 4G rápida, 3 cargas en frío (SwiftShader):
| Marca | Tiempo |
|---|---|
| FCP / LCP | 1,2–1,3 s / 1,7–2,0 s |
| JS transferido | 366 KB: `three.module.min.js` 163 KB (jsdelivr, llega a ~0,95 s), `construir.js` 47 KB, `moto3d.js` ~30 KB, `calcas_fabrica.js` 8 KB, addons |
| `modulo` (arranca el 3D) | 1,1 s |
| `armada` | 2,5 s |
| `boceto` | 2,8–3,2 s |
| `primerCuadro` | 3,8–5,0 s (compilación por software; en GPU real la sesión 3D midió ~1,7 s) |
Propuestas (ganancia estimada):
1. `<link rel="modulepreload">` para `three.module.min.js`, `moto3d.js` y `moto3d/construir.js` en la plantilla de la ficha:
   hoy se descubren en cadena (importmap → moto3d → construir); en 4G ≈150–300 ms menos hasta `modulo`.
2. Servir three.js desde nuestro propio dominio (copia fija 0.160.0 en `static/`): sin conexión TLS extra a jsdelivr
   (≈100–300 ms en 4G), Brotli (163 → ~140 KB) y caché inmutable compartida con la portada.
3. Minificar `construir.js` (165 KB, 46 KB gz) y `moto3d.js` (99 KB, 30 KB gz) en el build (p. ej. terser con Node, ya está en
   el build de Tailwind): ≈−35 % del peso transferido de esos archivos.
4. `moto3d-carga.js` (2 KB) es el único script que bloquea el análisis del HTML en todo el sitio: ver si puede ir con `defer`.
5. Despiece: el JSON de una moto (300 KB, 36 KB gz) y el público del diagnóstico cuestan **2–2,7 s la primera vez** tras
   reiniciar (después, 13–21 ms por la caché). Propuesta: calentar la caché del despiece en el build o en el cron diario;
   y `Cache-Control` corto (p. ej. 1 h) en `despiece_publico`, que no tiene datos de nadie.
Presupuestos de los auditores (sin bajar calidad): mantener ≤60 llamadas y ≤60 k triángulos por moto; **primer cuadro**:
boceto ≤1,5 s y cuadro real ≤2,5 s en escritorio con 4G rápida (≤3 s en Render, como ya pide el auditor); tareas largas
tras el primer cuadro ≤200 ms; **JS del 3D transferido ≤300 KB** (hoy 366 KB; con 2 y 3 queda ≈280 KB).

## Pendiente / propuestas generales (no hechas)
- **CSS por secciones**: 2/3 de `tallerya.css` no se usa en las páginas medidas. Separar los bloques de páginas propias
  (despiece/diagnóstico, panel del taller, cuenta/bienvenida, trámites) en hojas que carga solo su plantilla y borrar los
  ~36 KB de reglas sin clase viva (revisar antes las clases armadas en JS). No lo hice: otras sesiones editan `tallerya.css`
  y pide revisar visualmente página por página.
- `templates/base.html`: el ícono `icon-192.png` del final se descarga en todas las páginas aunque esté oculto →
  `loading="lazy"` (no toqué `base.html`).
- Fuentes de Google alojadas en el propio dominio: quita dos conexiones (googleapis + gstatic, ≈300 ms en 4G lenta) y el
  salto de fuente; requiere bajar los woff2 y tocar `base.html`.
- Sesiones `cached_db` solo cuando exista `REDIS_URL` (una consulta menos por página con sesión). Con caché local por proceso
  no es seguro (varios workers).
- Pregunta larga del foro: ~2 ms por respuesta en plantillas; solo vale la pena si los hilos pasan de ~100 respuestas.
