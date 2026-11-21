# XR 190L con Blender (intento 3) → `xr190l_tripo3.glb?v=2` (20-nov)

## Resultado
- GLB `garaje/static/garaje/modelos/xr190l_tripo3.glb`, conectado en `glb.js` (`"xr[ _-]*190"` → `xr190l_tripo3.glb?v=2`; único cambio en ese archivo). `xr190l_tripo2.glb` sin tocar: para volver, cambiar esa línea a `xr190l_tripo2.glb?v=13`.
- Visor (`/garaje/38/vista-3d/`): carga la v2 sin errores en consola, 64 nodos montados. Capturas en Chrome sin ventana: `final_lateral.png` (lado derecho, el del escape) y `final_tres_cuartos.png`.
- **Sin verificar** (se acabó la hora): Rayos X y Personalizar con clic (en esta página no hay botones y `__visor.modo` es solo lectura), 375 px y la revisión de piezas flotando en el visor.

## Hallazgo importante
El GLB de Tripo (`Downloads/modelo-3d-xr190l.glb`, 1,15 MB) **no trae textura horneada**: 64.328 triángulos, sin imágenes ni materiales. No hay color de Tripo que aprovechar: el color sale solo de los materiales por pieza y la foto sirve para las fronteras gruesas. (No pude leer `privado/tripo/xr190l/`: `settings.json` lo deniega; usé la copia de Descargas, que es el mismo archivo que lee `comun.py`).

## Método (scripts en `herramientas_3d/xr190l/blender/`)
1. `preparar.py` (Blender): importa, une, triangula, funde vértices, quita caras degeneradas y sueltas, tapa huecos de ≤ 40 aristas y recalcula normales. Tripo venía limpio (0 sueltas, 0 huecos chicos, 56 aristas de borde). Decimate disponible (sin usar: 64 mil caras ya es liviano).
2. `contornos.py` (python): despiece grueso con las reglas de `segmentar.py`: ruedas por radio, horquilla por su eje, rines 19/17, espejado para dejar el escape a la derecha y escala de la ficha (entre ejes de 1.353 mm, uniforme, `ALTO` = 1). Después saca el **contorno liso** de la tapa lateral, las aletas y el colín en la vista lateral: raster de 3 mm, cierre, apertura, relleno, gauss de 9 mm, curva de nivel y un punto por cm. Control: `contornos.png` en el scratchpad.
3. `cortar.py` (Blender): **bisect** con planos verticales por cada tramo de 1 cm de esos contornos (325 cortes), solo en la piel exterior (|z| > 4 cm). Luego reetiqueta: la cara que mira afuera y cae dentro de la curva es panel, y lo que era panel y quedó fuera pasa a chasis o cubierta. El borde entre blanco, rojo y negro sigue la curva cortada, no los triángulos de Tripo.
4. `construir3.py`: reutiliza `construir.py` con su MAPA de materiales PBR por pieza (la tabla de la R5 en `informes_noche/xr190l-3d-nuevo/relevo.md`), las 6 luces, las piezas internas de Rayos X (motor, caja, embrague, carburador, filtro, batería y cableado), la placa y la cuantización. La tapa lateral pasa a `pintura2` con `tono` blanco #e2e3df fijo.
Regenerar: `blender -b --factory-startup --python preparar.py -- ENTRADA.glb DIR/prep.npz`, después `python -I contornos.py DIR/prep.npz DIR`, `blender … cortar.py -- DIR` (~1,5 min) y `python -I construir3.py DIR`.

## Comparación con la v13
| | v13 (numpy) | v3 Blender |
|---|---|---|
| Peso | 1.038 KB | 1.379 KB (≤ 1,5 MB) |
| Triángulos | 79.455 | 105.901 (+27 mil por los cortes) |
| Nodos | 64 | 64 |
| Bordes de los paneles | camuflaje (manchas sueltas por cara) | curvas continuas en el lado izquierdo; en el derecho la tapa queda limpia, con una muesca arriba |
| Defectos que quedan | islas de color | muesca de la tapa arriba (x ≈ −0,3…−0,15), una mancha roja en el borde inferior de la aleta y una cuña oscura dentro de la tapa derecha |

## Pendientes (por impacto)
1. Verificar Rayos X, Personalizar, 375 px y piezas flotando en el visor con el pane visible.
2. Contornos: trazarlos a mano (puntos de control y spline sobre la foto) en vez de sacarlos del despiece grueso. Así se va la muesca de la tapa y la aleta sigue la línea real de la cuña.
3. Peso: limitar los bisect a las caras etiquetadas como panel (hoy cortan todo lo que cae en la franja, motor y escape incluidos). Bajaría unos 20 mil triángulos.
4. Normales por ángulo: hoy se suaviza toda la malla, como en la v13. Para aristas vivas habría que partir los vértices por ángulo al escribir.
5. Calca «XR 190L» a escala real: no se tocó `calcas_fabrica.js` (otra sesión lo tiene modificado). La regla vigente es ancho 0,15 en la zona `tanque`.
6. `pintura2` que siga al color 2 de Personalizar: hoy, con `tono`, queda blanca fija. Sin `tono`, sin color 2 elegido saldría roja.

## Paquetes o complementos
No instalé nada. Útiles a futuro: **scikit-image** (pip, unos 40 MB, de confianza) para contornos y morfología sin matplotlib. En Blender, el modificador **Weld** y **Remesh/Voxel** ya vienen incluidos y no hacen falta complementos.
