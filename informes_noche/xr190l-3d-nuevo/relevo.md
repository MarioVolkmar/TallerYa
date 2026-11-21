# Relevo XR 190L: ronda 1 de correcciones (20-nov)

Estado: GLB `xr190l_tripo2.glb?v=5` (1.037 KB, 79.455 triángulos, 64 nodos; la revisora tiene el aviso para medir la R3, la última). Regenerar con `python -I herramientas_3d/xr190l/segmentar.py` y después `construir.py`; render de control con `ver_despiece.py SALIDA --final --lado`, que da la vista derecha como las fotos. Correcciones de la revisora: `revision.md`. La sesión revisora es `local_57865e2e-4026-472b-9656-01c85a7f28dd`; quedan 2 rondas.

## Hecho en R1 (sin medir en el visor)
- **Espejo en z.** La moto quedó espejada en z: en el visor +z es la izquierda. Ahora la cadena va a la izquierda y el escape (cubierta negra bajo el colín) a la derecha. Ver `segmentar.py` main (B3).
- **Ruedas.** Rines 19/17 según la ficha. La llanta llega solo hasta R + 4 mm, para que el torneado del visor no se infle (B1).
- **Pintura por la foto.** `clase_foto()` proyecta cada cara en la foto lateral, calzada por los ejes en px (214,670) y (826,671), y la clasifica en rojo, blanco o negro dentro de la región de cada pieza. Después: voto entre vecinas y `quitar_islas` (B2).
- **Luces.** Faro, stop y 4 direccionales nuevos, cada uno con lente abombado y aro (`luces()` en `construir.py`). Las delanteras van fuera de la máscara (B4).
- **Calcas.** Quité mi `calcas_fabrica`, que estaba mal armada (`cara: "lados"`). Ahora se usa la regla de la XR 190 que ya existe en `calcas_fabrica.js` (B5, falta verificar).
- **Panel flotante.** La máscara lleva `rol: "visor_fijo"`, que esconde el visor genérico translúcido (I2).
- **Tambor trasero.** El «disco trasero» era la corona: ahora es `metal.corona`, pieza cadena (I3).
- **Horquilla.** Se parte en t = 0 (y ≈ 0,61): abajo plateada, arriba negra (I4).
- **Piezas nuevas.** Portaplaca, con la placa calculada desde su cara trasera, y estribos (I5).
- **Colores.** Aros y basculante pasan a `disco` (plateado claro), motor a `oscuro` y `M.blanco` queda en 0xeceae4 (la revisora pide un blanco frío de ≈ 196–200) (I1).

## Hecho en R2 (20-nov, sesión de relevo) → `?v=4`, verificado en el visor
- **Python:** el venv no tiene scipy; correr los scripts con el `python` del sistema (`python -I herramientas_3d/xr190l/segmentar.py` y luego `construir.py`, ~30 s en total).
- **Visibilidad al pintar** (`clase_visible()` en `segmentar.py`): z-buffer por celdas de 4 px de la foto (lado derecho = z < 0 en coordenadas de segmentar; el izquierdo se toma como espejo). Las caras ocultas heredan la clase de la cara visible más cercana sobre la malla (dijkstra). Esto arregló el colín (antes la cubierta de afuera se volvía roja y el colín de adentro, negro).
- **Rojo por tono**: `r > 55, r > 1,7 g, r > 1,5 b` (el rojo en sombra ya no se vuelve negro).
- `quitar_islas` con `minimo=150`.
- `M.blanco` = 0xc6c9cf en `glb.js` (solo lo usa la XR).
- Visor: `?v=4` carga, 0 errores, `fabrica()` = 1.533 vértices (calcas visibles), 6 luces separadas, escape a la derecha (+z del visor; segmentar usa z < 0 porque el GLB voltea z).
- Revisora avisada para medir la R2.

## Hecho en R2 de la revisora → `?v=5` (verificado: carga y 0 errores)
- `glb.js`: `extras.tono` / `acabado` / `emisivo` clonan el material solo para esa pieza (no toca otras motos). Úsese solo en piezas que Personalizar no recolorea.
- Tonos calculados en lineal: base × (meta / render medido), con la tabla R2 de `revision.md`: asiento, tanque, cubierta, escape, motor, amortiguador, basculante (metalness 0,3) y el stop (mica #b3121a, emisivo #ff0a0a).
- Llantas: 90 mm de ancho adelante y 110 atrás; adelante 6 mm menos de radio; el balón sobrante se etiqueta `_balon` y se descarta (`construir.py` solo arma lo que está en MAPA).

## Cierre de rondas (20-nov)
La R3 definitiva midió la **v5**: color 33 % (4/12; otras 3 en ΔE 5,3–5,7), IoU lateral 0,836 (0,924 con huecos rellenos); luces y Rayos X cumplen. Detalle en `revision.md`, «Ronda 3 … v5». Para medir sin revisora: scripts en la carpeta de notas compartidas `revisora-xr190l/` (LEEME.md).

## Ronda 4 (20-nov, sesión de modelado) → `?v=10`, medido con el método de la revisora
- **Medido**: color **100 %** (12/12, todas ΔE ≤ 3,5), IoU lateral sin sombra **0,8505** (relleno 0,935). Carga sin errores, 1.037 KB.
- **Colín negro**: era el escape **genérico del visor** (cilindro negro con banda plateada) montado encima del colín. Ahora el escape del GLB lleva `padre: "escapeFabrica"` y lo reemplaza.
- **Chasis**: `glb.js` vuelve el chasis con `tono` el «chasis a la vista» (`M.chasisVisto`, tono #464a54): Personalizar lo deja de fábrica o le pone el color elegido.
- **Aros**: `tono` #d7e1f8 (no llevan `aro`, así que Personalizar no los toca). Asiento #17202f, basculante #ecf0ff, escape #454b58, `M.blanco` 0xb5bbca.
- **Rojo**: rojo de fábrica de la XR 190 pasa a #e41c30 (`colores_fabrica.py`) y la moto 38 de prueba quedó con ese color. Nuevo `extras.luz` en `glb.js` (factor de brillo que sigue el color de Personalizar): colín 0,47 (a la sombra del asiento en la foto) y guardabarros 0,72.
- **Silueta**: `ALTO = 1,03` en `construir.py` (el Tripo salía ~3 % bajo frente a la foto; 1,015 da 0,846, 1,045 da 0,836). Espejos: cabezas +5 cm adelante y +4,5 cm arriba, con el tallo estirado desde el manubrio.
- **Calca**: «XR 190L» en una línea, ancho 0,15. Más ancha se recorta: la ventana visible de la zona `tanque` mide unos 15 cm (falta ver de dónde sale ese recorte para llegar al 60 % de la aleta).
- Medición propia: `revisora-xr190l/modelado/` en la carpeta de notas (`cap.js` se sirve en el proxy como `/__cap.js`; la pasada de ID esconde las mallas sin nombre, porque los grupos unidos del visor tapaban las piezas).

## Ronda 5 (20-nov, pintado por materiales) → `?v=13`
- **Enfoque**: cada pieza lleva el material de lo que es en una XR 190L real (`MAPA` en `construir.py`: `tono` + `acabado`), color limpio de fábrica; se quitaron los `luz` 0,72/0,47 (sombras de la foto) y los tonos azulados calcados del render. No hay textura horneada: el color es uniforme por pieza.
- `glb.js`: `acabado` sin `tono` clona el material compartido y copia el color de Personalizar en cada cuadro (las piezas rojas siguen el color elegido con su propio acabado). El chasis acepta `acabado`.
- **Sin estirar** (`ALTO = 1.0`): alto según la ficha. Las cabezas de los espejos siguen +4,5 cm.
- `segmentar.py`: `quitar_encerradas` (manchas negras rodeadas por panel → panel) y «chasis» que mira hacia afuera en la zona de aletas y tapa → panel. Efecto chico (+118 caras de tapa). Copia de la v10: `segmentar_v10.py` y `despiece_v10.npz` en el scratchpad de la sesión (se pierden al limpiar).
- Verificado: carga v13, 0 errores, 1.038 KB, 64 nodos. Capturas: `materiales_lateral.png`, `materiales_tres_cuartos.png`. **Sin verificar**: Rayos X, 375 px, ΔE e IoU (ya no son el criterio).

| Pieza | Material | Color | Rough. | Metal. |
|---|---|---|---|---|
| Aletas, máscara, guardabarros del., colín | plástico inyectado brillante (PP), sigue a Personalizar | rojo de fábrica #e41c30 | 0,36 (+barniz 0,35) | 0 |
| Tapa lateral | plástico inyectado blanco | #e2e3df | 0,38 (+barniz 0,3) | 0 |
| Tanque | pintura negra sobre acero | #141518 | 0,28 (+barniz 0,8) | 0,05 |
| Chasis, manubrio, parrilla | pintura negra sobre acero | #1e2023 / #1d1f22 | 0,28 (+barniz 0,8) | 0,05 |
| Cubierta trasera, guardabarros tras., portaplaca | plástico negro mate texturizado | #1c1d1f | 0,78 | 0 |
| Asiento | vinilo | #151617 | 0,62 (+barniz 0,2) | 0 |
| Llantas, puños | caucho | #181818 | 0,88 | 0 |
| Aros | aluminio | #c6cacd | 0,34 | 0,85 |
| Rayos | acero cincado (cromo del visor) | #f2f4f5 | 0,05 | 1 |
| Disco / corona | acero | #9da2a6 / #8f9498 | 0,42 / 0,45 | 0,9 |
| Horquilla baja | aluminio fundido | #b9bdc0 | 0,40 | 0,75 |
| Horquilla alta (fuelles) | caucho/plástico negro | #1b1c1e | 0,72 | 0 |
| Basculante | acero pintado plateado | #b4b8bc | 0,36 | 0,6 |
| Motor | aluminio pintado negro | #2b2d30 | 0,48 | 0,45 |
| Escape | pintura negra de alta temperatura | #202124 | 0,62 | 0,25 |
| Amortiguador, estribos | acero negro | #1f2023 / #1d1f22 | 0,5 / 0,6 | 0,3 |
| Espejos | plástico negro | #18191b | 0,45 | 0 |
| Faro, stop, direccionales | sin cambio (mica + emisivo) | stop #b3121a / #ff0a0a | — | — |

**Falta (lo que más resta ahora)**: los bordes entre paneles siguen como camuflaje (manchas blancas, negras y rojas en tapa y aleta), porque la división de la carrocería sale del color de la foto (`clase_visible`). Siguiente paso: definir tapa lateral y aletas por geometría (un panel continuo, p. ej. crecer desde una semilla por normal y curvatura) y usar la foto solo para la frontera gruesa. Luego calca a escala y `pintura2`.

## Falta (por orden de impacto)
1. Calca: el recorte de la zona `tanque` (ver arriba); en la foto, «XR» va arriba y «190L» grande abajo.
2. Bordes de la tapa lateral (bumerán liso, sin isla oscura) y del colín: no se tocaron en la R4.
3. Margen de IoU (0,8505): lo que más resta son los rayos, la sombra de contacto de la foto bajo las llantas y las cabezas de los espejos, más delgadas que en la foto.
4. Sin verificar en la R4: `pintura2` en la tapa lateral, Rayos X y 375 px.

## Falta antes de la R4 (histórico)
1. Colín de lado casi negro (ΔE 23): forzar `colin` en la banda roja bajo el asiento y en la cara superior de la cola (la regla `parrilla`, y > 0,93 no rojo, se lo come).
2. Chasis y aros sin tono propio (ΔE 12 y 11): Personalizar los recolorea; hace falta un tono de fábrica que Personalizar respete (no un clon fijo).
3. Rojo oscuro (170 contra 200): sale del color de la moto 38 (M.pintura), no del GLB.
4. Tapa lateral, asiento y basculante algo cálidos: +1–2 puntos de azul en su tono.
5. Borde de la tapa lateral (bumerán liso, sin isla negra).
6. Calca «XR 190L» grande en diagonal (`calcas_fabrica.js`) y espejos más altos y atrás.
