# Medición: herramientas y trampas

| Archivo | Qué da | Costo |
|---|---|---|
| `servidor.py URL… --usuario correo URL…` | ms (mejor de 3), consultas, repetidas, KB y KB gzip del HTML/JSON; `--top N` las SQL repetidas | ~10 s, 1 línea por URL |
| `medir_chrome.py base ruta… [--celular] [--usuario]` | por carga fría y tibia: TTFB, FCP, LCP (+ elemento), load, esquema, 3D listo, tarea larga máx., KB | ~15-40 s por URL |
| `medir.js` | lo mismo, en `javascript_tool` (Browser pane visible) o desde `medir_chrome.py`; detalle en el JSON: `porTipo`, `grandes`, `tresD.tiempos` | 1 KB de salida |
| `pesos.py medicion.json` | KB bruto / gzip / brotli por tipo con tope ✗, y los más pesados | ~5 s |
| `traza.py url [s] [correo]` | las 6 tareas más largas del hilo principal y qué las llena (375 px, CPU ×4, sin freno de red) | ~20-40 s |
| `sesion.py correo` | línea JS de cookie de sesión para el Browser pane (sin contraseña, solo local) | — |

## Cómo leer `tresD.tiempos` (ms desde la navegación)
`modulo` (arrancó moto3d.js) → `escena` → `armada` (piezas) → `unido` → `boceto` (primer cuadro sin sombras) →
`compilaAsync` → `compilado` → `listo` → `reflejos` / `sombras`. Huecos típicos:
- `modulo` tarde: el JS tardó en llegar o el hilo estaba ocupado antes (ver la traza).
- `armada − escena` grande: armado (CPU); `msArmado`, `etapas` y `pedazoMasLargo` dicen cuál.
- `compilaAsync − boceto` grande **solo en frío**: espera de GPU compilando shaders (en tibio, la caché de shaders lo borra).
- `calidad`: `alta`/`baja` según el equipo (en 375 px sale `baja`).

## Trampas conocidas
- **Pestaña oculta** → rAF frenado → 3D falso. `medir_chrome.py` usa `--headless=new` (visible) y GPU real (`--use-angle=d3d11`);
  `--gpu swiftshader` solo si no hay GPU (no comparable).
- **Git Bash** convierte `/talleres/` en `C:/Program Files/Git/talleres/`: los scripts lo deshacen solos; en otros comandos,
  `MSYS_NO_PATHCONV=1`.
- **Servidor 8001** con autorrecarga: esperas de 10-50 s cuando otra sesión guarda. Medir en `tallerya-medir` (8024).
- **LCP vacío** (`null`): la página no registró candidato (p. ej. texto que entra con animación de opacidad). Usar FCP y
  revisar el elemento a mano; no es un 0.
- **Esquema `≤x (ya estaba al medir)`**: `medir.js` se corrió tarde; volver a medir con `navigate` + script en el mismo batch.
- **KB por red en desarrollo** = sin comprimir: usar `pesos.py`.
- Variación: la 1.ª corrida del día compila Python y llena cachés; descartarla si se ve atípica.
