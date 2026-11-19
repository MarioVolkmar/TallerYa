---
name: optimizar-velocidad
description: Mide y acelera la carga de TallerYa a fondo (páginas, esquema o despiece, visor 3D) contra un presupuesto de celular con 4G. Mide en Chrome sin ventana o en el Browser pane (FCP, LCP, esquema visible, 3D listo, tareas largas, pesos comprimidos) y en el servidor (ms y consultas por URL); prioriza por impacto y esfuerzo, aplica y vuelve a medir con tabla de antes y después. Úsala cuando pidan «está lenta», «optimizar», «acelerar la carga», «¿cuánto tarda en el celular?», o tras cambios que afecten la carga (JS, CSS, plantillas base, vistas con listas, 3D, despiece). Para el chequeo rápido antes de desplegar ya está la parte de velocidad de revisar-seguridad.
---

# Optimizar velocidad (TallerYa)

Rutas relativas a la raíz. `V` = `.claude/skills/optimizar-velocidad`. Casi todos entran **por celular y con datos**:
manda el perfil «celular de referencia» (375 px, CPU ×4, 4G a 150 ms y 9 Mbps, carga fría).
**Meta de la sesión:** auditoría de una página en **≤ 10 min** y **≤ 2 capturas**; cada cambio, con una tabla de antes y después.

## Reglas fijas
- **No dupliques `revisar-seguridad`**: su `--solo velocidad` es el chequeo rápido antes de desplegar. Esta skill es la de fondo.
- **Medir antes de tocar** y guardar el «antes» (`--json` en el scratchpad). Sin número no hay arreglo.
- **Pestaña visible.** Una pestaña oculta frena `requestAnimationFrame` y el 3D sale con tiempos falsos (ya pasó). Mide con
  `medir_chrome.py` (Chrome sin ventana: cuenta como visible) o, en el Browser pane, solo si `tabs_context` dice
  «displayed». `medir.js` devuelve `aviso` si la pestaña estaba oculta: esa medición no vale.
- **Servidor propio sin autorrecarga** para medir: preview `tallerya-medir` (127.0.0.1:8024, `--noreload`). El 8001 se
  reinicia cada vez que otra sesión guarda un `.py` y mete esperas de 10 a 50 s.
- **runserver entrega los estáticos sin comprimir** (y el JS 3D sin minificar: en producción va `build_js/`). Los KB «por red»
  del servidor de desarrollo no sirven para el presupuesto: los pesos se miden con `pesos.py` (gzip/brotli como WhiteNoise).
- **Ruido:** mínimo 2 corridas por caso; si dos difieren más de 30 %, repetir. Con otras sesiones usando la máquina,
  intercalar antes y después (A, B, A, B).
- **No romper nada visual:** tras cada cambio que se ve, `revisar-ux` (script a 1280 y 375 px). El 3D y el esquema se
  comprueban abiertos (no solo «cargó»).
- Coordinación: el 3D (`moto3d*.js`, `construir.js`, `glb.js`) suele estar en un worktree de otra sesión; los dibujos
  (`diagramas.py`) son de la sesión de dibujos. Proponer allí, no editar sin avisar. Sin commit salvo que lo pidan.

## 1. Medir (≈ 3 min)
```bash
P=venv/Scripts/python.exe; B=http://127.0.0.1:8024; S=<scratchpad>
$P V/servidor.py / /talleres/ /mecanicos/ --usuario <correo> /garaje/3/ /garaje/3/despiece.json --top 3 --json $S/srv.json
$P V/medir_chrome.py $B / /talleres/ /mecanicos/ --celular --json $S/pub.json          # 375/4G×4, fría y tibia
$P V/medir_chrome.py $B /garaje/3/ --usuario <correo> --celular --json $S/moto.json
$P V/medir_chrome.py $B /garaje/3/ --usuario <correo> --json $S/moto_pc.json             # 1366 sin freno
$P V/pesos.py $S/moto.json                                                               # KB br por tipo vs tope
```
- `--usuario` crea una sesión de Django **sin contraseña** (solo servidores locales). `--celular --sin-freno` = solo 375 px,
  para comparar con mediciones viejas sin freno. `--veces 1` = solo fría.
- Browser pane (si está visible): `sesion.py <correo>` imprime la línea de cookie; luego en **un** `browser_batch`:
  `navigate` → `javascript_tool` con el contenido de `V/medir.js` (espera el load, el esquema y el 3D; máx. 20 s).
- ¿Una tarea larga sin explicación? `$P V/traza.py $B/garaje/3/ 30 <correo>`: las 6 tareas más largas y qué las llena
  (Layout, un JS concreto, GPUTask, GC). Herramientas y trampas: `anexo-medicion.md`.

## 2. Comparar con el presupuesto
Tabla con una fila por medida: **base · ahora · meta · tope · ✓/✗**. Presupuestos y línea base en `anexo-presupuesto.md`.
Lo que pase el **tope** es prioridad; lo que esté entre meta y tope, mejora.

## 3. Priorizar
Por cada ✗, la causa (con evidencia: recurso, traza, consulta) y una técnica de `anexo-tecnicas.md`. Ordenar por
**impacto en segundos del celular de referencia ÷ esfuerzo** (S < 1 h, M < medio día, L más). Primero lo que bloquea el
primer pintado (CSS, fuentes, HTML del servidor), luego lo que bloquea la interacción (tareas largas), al final el peso.

## 4. Aplicar y volver a medir
Un cambio a la vez (o un grupo pequeño con un mismo objetivo), con la misma corrida del paso 1. Si no mejora al menos
10 % la medida que buscaba, revertir. Pruebas: las focalizadas de la app; si tocó vistas, `assertNumQueries`.

## 5. Autocontrol (antes de decir «listo»)
- [ ] Antes y después medidos con el mismo perfil, servidor 8024, pestaña visible, ≥ 2 corridas.
- [ ] Tabla contra presupuesto con la línea base del anexo actualizada si hubo mejora.
- [ ] `revisar-ux` sin hallazgos nuevos; esquema, 3D y Personalizar abiertos a mano a 375 px (un `read_page` o una captura a escala 0,5).
- [ ] Pruebas focalizadas verdes; ningún archivo de otra sesión tocado sin avisar.
- [ ] Informe en `informes_noche/<tema>.md`: causas, cambios, tabla antes/después, pendientes.


## Ahorro de tokens
Registros largos (render, IoU, builds, pruebas, mediciones) a un archivo en el scratchpad; mostrar solo el resumen (`> log.txt; tail -15 log.txt`). Capturas solo como prueba final, a `scale: 0.5`. Tope de ~150 mil tokens de contexto: al llegar, nota de relevo y sesión nueva (ver CLAUDE.md, «Modelo según la tarea»).
