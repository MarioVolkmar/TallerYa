# L4 · Bajaj Boxer CT100 (TEC): carburador PB-16 (fig. 16)

Lámina `boxer-carburador`:
- página: `motor/boxer-carburador.html`;
- archivo único: `motor/prueba-boxer-carburador.html` (901 KB).

**Sin hermana.** Del catálogo usé solo la plantilla de fichas y el estilo de la CVT.

**Figura:** el catálogo trae tres carburadores:
- 16, PB-16 (TEC-S1D): es la que usé, columna TEC;
- 16A, Keihin (UG-4T);
- 16B, Keihin (K-TEC).

Las 16A y 16B son de versiones anteriores.

**Números:** 19 en el dibujo. Los 4, 6 y 22 son kits:
- kit del carburador;
- flota y aguja;
- sensor completo.

## Tiempo (`metricas.py`, de 23:32 a 23:55)
| fase | real | presupuesto | |
|---|---|---|---|
| catálogo + esqueleto | 3 | 1,5 | ⚠ |
| dibujo + contenido | 9 | 4 | ✋ más del doble |
| validación + mediciones | 3 | 2,5 | ⚠ |
| revisión (correcciones) | 8 | 1,5 | ✋ más del doble |
| **total con revisión** | **23 min** | 10 | faltaron 13 |

- La revisora corrió 2 min en paralelo con la primera medición `--final`.
- **Mediciones completas: 4.** Ninguna tuvo bloqueantes, pero las tres primeras dieron «NO APRUEBA» por el criterio 6 (ver «Qué falló»). La cuarta aprueba.
- **Imágenes: 4**, una más que el tope de 3. Fueron el plano equivocado que entregó `esqueleto_v2`, el plano correcto, la previa y la captura final.

## Tokens
- **Creación:** ≈ 128 mil (el contexto pasó de 123 mil a 251 mil).
- **Revisora (una, opus):** 91 mil.

## Notas
- **Medible:** 4,82. Por criterio: 6 = 5, 8 = 4,3, 9 = 5, 10 = 5, 11 = 4,8 y 12 = 4,8. Sin bloqueantes.
- **A ojo:**
  - 4 en los criterios 1, 2, 4, 5 y 7;
  - 5 en el criterio 3, por «Cómo funciona»: 6 pasos con corte, flota que sube, cortina y aguja que suben, rocío por el boquerel y el chiclé, rebose, y barras de acelerador y nivel.
- **Revisora, antes de corregir:** mecánica 4,0 y UX 4,3.
  - No llega a 4,8. Corregí todos los graves, pero sin una segunda revisión la nota después de corregir no está medida.
  - La causa: sin hermana y sin manual de servicio, varias cadenas culpaban al eslabón equivocado.

## Hallazgos (15: 5 graves, 10 menores; 0 falsos)
**Por script (`aplicar_hallazgos.py`), 14.** Ajusté uno antes de aplicarlo: la revisora quitaba del paso 0 «que nada gotee», y eso rompía el control de gasolina del validador. Lo dejé así: «la cortina entra en su guía, el acelerador vuelve solo y nada gotea». Los graves:
- dos eslabones de cadena no causales:
  - culpaban a la flota en vez de a la aguja rayada;
  - culpaban al o-ring en vez de al aislador;
- cerrar el tornillo de aire «suave, sin forzar»;
- ficha 7: es el tornillo de aire del circuito de baja (manual, p. 17), no «cerca del chiclé».

**A mano, 1** (el grupo «Cuerpo y taza» lista el 1 dos veces). Lo intenté y lo revertí:
- sacar el cuerpo del grupo da el error «pieza sin grupo»;
- pasarlo a otro grupo no ayudó.

Quedó en `pendientes`. Los reemplazos se vuelven a aplicar solos: el script de armado llama a `--reaplicar`.

## Qué falló y propuestas (sin aplicar)
1. **Paso 1, catálogo. `extraer_catalogo.py --figura 16` no encuentra la tabla**, porque la expresión de `figura_generica` no acepta un paréntesis con letras: «CARBURADOR (TEC-S1D)».
   - Lo resolví con un parser en el scratchpad (`extraer_fig16.py`) que importa el extractor y cambia solo esa expresión.
   - Ese parser tomaba también las páginas 44-46 (16A y 16B). Lo corregí a mano a `paginas:[43]`.
   - *Propuesta:* aceptar `\([^)]*\)` como fin del título y no tomar «16A» como «16».
2. **«Para ver la lámina» (Reglas fijas). El «plano:» de `esqueleto_v2.py` era la página 42 (fig. 15 2/2)**, la página antes de la tabla, como en Yamaha. En Auteco, el plano va en la misma página que la tabla. Gasté una imagen.
   - *Propuesta:* que use la página de la tabla cuando el catálogo es de tipo genérico (Auteco).
3. **Paso 3 y criterio 6. Un número repetido en dos grupos rompe el toque en escritorio**, y nada lo avisa antes de la medición:
   - el o-ring de la tapa (5b, n 5) iba en «Tapa» y el empaque de la taza (5) en «Cuerpo»;
   - a 1024/1280, ninguna pieza de esos dos grupos se dejaba seleccionar, probablemente porque tocar el 5 cambia de grupo;
   - me costó 2 mediciones `--final`. Lo arreglé sacando el 5b del dibujo.
   - *Propuesta:* que el validador (`--rapido`) dé error si un mismo `n` aparece en dos grupos.
4. **Paso 3, piezas internas. `ocultas` no esconde el arte propio**: hace falta la clase `esq-oculto-arm` en el `<g>`. La skill lo dice en «Piezas internas», pero el esqueleto llena `ocultas` y parece que basta con eso. La previa mostró el chiclé encima del cuerpo.
   - *Propuesta:* que `--rapido` avise si una pieza de `ocultas` con arte propio no lleva la clase.
5. **Formato de `encuadreArmado`: es `[x, y, ancho, alto]`.** Lo escribí como `[x0, y0, x1, y1]` y el error de proporción no dice cuál es el formato.
   - *Propuesta:* poner el formato en el mensaje del validador.
6. **Tiempo (Plan de 10 min). Sin hermana, una pieza compleja no entra en 4 min de dibujo**: fueron 15 funciones de arte, la animación con 6 estados y 19 fichas.
   - *Propuesta:* un presupuesto «sin hermana» de dibujo + contenido de 7 min. O empezar una biblioteca de carburación (cuerpo, cortina, aguja, chiclé, flota) en `piezas-comunes.js`, que sirva para la próxima lámina de carburador (Keihin 16A/16B, AKT, Honda).
7. **Revisora. Para el criterio 6 sugirió «1-taza», pero eso ya existía (`1t`).** Su hallazgo de dibujo no se podía aplicar como estaba escrito.

**Datos sin fuente (en `pendientes`):**
- número de los chiclés, vueltas del tornillo de aire y nivel de la flota: sin manual de servicio;
- ralentí 1.300 rpm y la tabla de limpieza: del manual del propietario BS VI de India, otra versión;
- función del imán 13, que el catálogo llama «imán swiche gato lateral».

**Auditoría:** `metricas.py` avisa que hay una auditoría externa pendiente: lleva 8 láminas sin auditar. No creé `auditoria-pendiente.md`; ya existía.

Sin commit.
