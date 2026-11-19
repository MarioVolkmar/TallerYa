# Presupuesto de rendimiento

**Celular de referencia** (manda): `medir_chrome.py --celular` = 375×812, DPR 2, toque, CPU ×4, 4G (150 ms, 9 Mbps
bajada, 3 Mbps subida), carga **fría** (perfil nuevo: sin caché de red ni de shaders). Tiempos en s desde la navegación.
Medido en el servidor de desarrollo (estáticos sin comprimir: los tiempos de red son algo peores que en producción, así que
cumplir aquí es cumplir allá). El 3D depende de la GPU, que el freno de CPU no frena: equipo de referencia Intel UHD.

## Tiempos
| Medida | Dónde | Meta | Tope | Base 19-nov-2026 (fría) |
|---|---|---|---|---|
| FCP (primer pintado) | todas | ≤ 1,8 | 3,0 | portada 2,8 · talleres 2,8 · mecánicos 2,5 |
| LCP (contenido principal) | todas | ≤ 2,5 | 4,0 | portada 2,8 · talleres 2,9 · mecánicos 4,6 |
| Esquema visible (`.despiece-listo` + `<img>` cargada) | `/garaje/<id>/` | ≤ 3,0 | 6,0 | 20,0 (375 sin freno: 4,4 · 1366: 4,1) · **19-nov tarde: 1366 2,5 · 375 sin freno 4,5** |
| 3D listo (`__visor.info().tiempos.listo`) | `/garaje/<id>/` | ≤ 4,0 sin freno de CPU · ≤ 12 con ×4 | 8 · 20 | 375 sin freno 7,1 · ×4: 37,3 · 1366: 11,8 · **19-nov tarde: 1366 6,8 · 375 sin freno 8,0** |
| 3D listo, tibia (segunda visita) | `/garaje/<id>/` | ≤ 2,5 | 4,0 | 375 sin freno 2,8 · 1366: 5,7 |
| Tarea larga máxima | todas | ≤ 0,5 | 1,0 | portada 5,0 · talleres 2,8 · mecánicos 1,5 · moto 4,3 · **19-nov tarde, moto 1366: 1,2 (antes 2,7)** |
| Suma de tareas largas | `/garaje/<id>/` | ≤ 3 | 8 | 18,8 |

## Pesos (comprimidos con brotli, primera visita; `pesos.py`)
| Tipo | Meta por página | Tope | Base (moto 3 / portada) |
|---|---|---|---|
| JS | ≤ 50 KB sin 3D · ≤ 250 KB con 3D | 80 · 350 | 283 (three 132) / 14 |
| CSS (bloquea el pintado) | ≤ 40 KB | 60 | 81 (`tallerya.css` 69) / 80 (sin minificar) · **19-nov tarde, como en producción (minificado): 59 / 53** (base 38 + sección) |
| HTML (gzip) | ≤ 25 KB | 40 | 35 / 24 |
| JSON inicial del despiece | ≤ 30 KB | 40 | 32 (217 bruto) |
| SVG por dibujo | ≤ 40 KB | 60 | 35 (230 bruto) |
| GLB por modelo | ≤ 400 KB | 600 | 400 (`nmax155.glb`, solo con `?modelo3d=glb`) |
| Imagen arriba del pliegue | ≤ 100 KB c/u | 150 | ok |

## Servidor (`servidor.py`, mejor de 3, base local)
| Medida | Meta | Tope | Base |
|---|---|---|---|
| ms por página | ≤ 150 | 300 | portada 141 · talleres 127 · mecánicos 93 · moto 338 · despiece.json 87 |
| Consultas por página | ≤ 20 | 35 | 15 · 12 · 11 · 39 · 13 |
| Consultas repetidas (misma SQL) | 0 | 2 (3 o más = N+1) | moto: 1 (`reglapicoplaca` ×2) |

Los topes de servidor son los mismos avisos de `revisar-seguridad` (300 ms, 35 consultas): mantenerlos iguales.
Al mejorar algo, **actualizar la columna Base** con la fecha.
