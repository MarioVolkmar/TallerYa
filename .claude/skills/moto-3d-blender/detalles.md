# moto-3d-blender: detalles y trampas

## Scripts (`scripts/`)
| Script | Corre en | Qué hace |
|---|---|---|
| `armar.py` | Python `-I` o Blender (`-b --python armar.py -- ficha.json`) | Lee el Tripo despiezado (orden de vértices = el de la página de etiquetas), gira y escala, reparte por etiquetas, ruedas, luces, placa, internos y escribe el GLB del visor con `glbio.escribir` (int16/int8, `KHR_mesh_quantization`, `extras` por nodo y `modelo_completo` en la escena). Deja `fichas/<moto>.armado.json`. |
| `revisar.py` | Python `-I` | Chequeos (abajo) + `npx gltf-transform validate`. Código 1 si falla. |
| `resumen.py` | Blender 5.3 `-b --factory-startup --gpu-backend opengl` | Importa el GLB, colores aproximados por prefijo, 6 vistas Eevee (lateral izq/der, frente, atrás, 3/4, luces encendidas) y compone `resumen.png` con las fotos (render | foto). |
| `correr.py` | Python `-I` | Los tres en orden. Un solo Blender a la vez (8 GB de RAM). |
| `capturar.py` | `venv/Scripts/python.exe` (usa `optimizar-velocidad/medir_chrome.py`) | Capturas del visor real en Chrome sin ventana. |
| `glbio.py` | — | Lee y escribe el formato del visor. |

## Etiquetas → material
- Zona por triángulo con borde suavizado (isolínea 0,5 de la pertenencia por vértice); lo sin pintar = zona 0 (su texto es el de la parte o el de la zona 0).
- Texto → (pieza, acabado) con `garaje/deduccion_3d.deducir` y dos reglas encima: «principal / color moto» = `pintura`, «secundario» = `pintura_secundaria` (la deducción de la página pone «plástico» antes que «color principal»).
- Acabado → prefijo del visor: pintura→`pintura` (Personalizar), pintura_secundaria→`blanco`, plastico_mate→`plastico` (`chasis` si es basculante), plastico_brillo→`negro_brillo`, caucho→`caucho`, vinilo→`asiento`, cromo→`cromo`, aluminio→`metal` (`carter` en motor/cvt), motor→`motor`, mica_ambar→`ambar`, mica_roja→`stop`, mica_faro→`luz` en el faro y `vidrio_oscuro` en el visor, oculta→fuera. En `forzar` se puede poner el material directo: `"pieza/@oscuro"`.
- Un PBR por material (`ACABADO` en armar.py): todos los nodos del mismo material llevan el mismo `extras.acabado`.
- Nodos agrupados por (material, pieza): `pintura.carenado`, `plastico.piezas`… Partes de >60 mil vértices se parten (uint16).
- Extras: `rueda`+`pieza`+`eje` en llanta, rin y disco (la traslación del nodo es el eje = pivote); `lampara {tipo}` en luces; `placa {c, incl, tam}`; `padre` (escape → `escapeFabrica`, espejo → `espejos.fabrica`); `pieza` para mantenimiento (horquilla, amortiguador, motor); `zonas` en pintura lateral y guardabarros (calcas).

## Revisión (`revisar.py`)
- Flotantes: rejilla de 2 cm; una pieza sin vecinos de otra pieza falla.
- Translúcidas (`vidrio`, `vidrio_oscuro`, `mica_dir`) solo si el nombre dice visor, faro, mica, parabrisas o tablero.
- Un material = un tono: mismos `tono`, `acabado`, `luz`, `emisivo`.
- Ruedas: llanta y rin con el mismo eje; hueco talón–pestaña ≤ 12 mm; rin centrado (≤ 6 mm); rin dentro del ancho de la llanta.
- Placa presente; luces: ≥1 faro (`luz` o `luz_reflector`), ≥1 stop (`stop`), 4 direccionales (`ambar`) en los cuatro lados.
- Peso ≤ 1,5 MB.
- `gltf-transform validate` sin errores.

Trampas: `trampas.md`.
