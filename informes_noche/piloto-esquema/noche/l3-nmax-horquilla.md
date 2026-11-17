# L3 · Yamaha NMAX 155 (BBE4, 2024): horquilla y dirección (fig. 18)

Lámina `nmax-horquilla` · página `motor/nmax-horquilla.html` · archivo único `motor/prueba-nmax-horquilla.html` (934 KB). Hermana: `cb125f-horquilla` (Honda F-8), remapeada con `remapear_hermana.py`.
**Alcance:** la fig. 18 «Steering» no es solo la horquilla. Trae 53 números: las dos barras (2-17 y 18-33), la tija inferior y los cojinetes de la dirección (34-49) y las pinzas de la manguera (50-53). Dibujé los 50 números con pieza; 1, 2 y 18 son kits. La barra derecha es el espejo de la izquierda (x → 780 − x) y la dirección va en el centro.

## Tiempo (según `metricas.py`)
| fase | real | presupuesto |
|---|---|---|
| catálogo | 2 | 1,5 ⚠ |
| dibujo + contenido | 6 | 4 ⚠ |
| validación + medición | 2 | 2,5 |
| revisión (correcciones) | 3 | 1,5 ⚠ |
| **total con revisión** | **≈ 13 min** de trabajo (16 de reloj según `metricas.py`); la revisora corrió 3 min en paralelo | 10 |

**Mediciones completas: 1** (`--final`, sin bloqueantes). Después, solo `--previa --solo-solape`, porque moví piezas del despiece.
**Tokens:** creación ≈ 98 k (de 122 k a 220 k de contexto; el inicio es estimado porque no lo medí al empezar). Revisora: 108 k.
**Imágenes: 1** (la previa a 900 px). El plano no lo miré: no hay grilla de la fig. 18 (ver «Qué falló»).

## Notas
- **Medible:** 4,57, con el criterio 6 en 4,5, 8: 4,0, 9: 4,3, 10: 5,0, 11: 4,8 y 12: 4,8. Sin bloqueantes.
- **A ojo:** 4 en los criterios 1, 2, 3, 4, 5 y 7.
- **Revisora, antes de corregir:** mecánica 3,5 y UX 3,9. **No llega a 4,8**: todo lo grave eran restos de la Honda y lo corregí. No pedí una segunda revisión, así que la nota después de corregir no está medida.
- **Avisos que quedan:** «Desarmar» queda fuera de la pantalla al entrar a un grupo (1024/1280, es del motor). Tres toques de 20 px a 360 (piezas 6, 10 y 26).

## Hallazgos (15: 9 graves, 6 menores; 0 falsos)
- **Por script (`aplicar_hallazgos.py`), 8:** los pernos de la tija se aflojan en el paso del tapón; la NMAX no tiene tija de arriba (pasos 0 y 7); el aviso de sujetar la tija va antes de soltar las tuercas; la pinza 52 es la derecha (y su tornillo 53); «Va nuevo cada vez» en el seguro del tapón; «barras torcidas» en vez de «chuecas».
- **A mano, en el script de armado, 7:**
  - el **gato central no levanta la rueda delantera**: la moto va calzada bajo el chasis (grave; el aplicador no lo puso porque el campo tenía dos reemplazos);
  - o-ring → empaque (GASKET) en las dos barras;
  - «asiento» → amortiguador en «Cómo funciona» y en 10, 11, 13, 9 y sus pares derechos;
  - «conecta» de 52 y 53, y concordancia en 12 y 28;
  - la tapa 43 pasó al grupo de la tija y al paso de la tija.
- **Sin corregir (a `pendientes`):** el orden de pistas, jaulas y tapas de la dirección (36-44) viene de los nombres del catálogo, no del plano.

## Qué falló y propuestas (sin aplicar)
1. **«Para ver la lámina» (Reglas fijas):** no existe `despiece_local/grillas/Yamaha-NMAX_155-BBE4-fig18.png`, así que dibujé la dirección sin ver el plano. *Propuesta:* que `esqueleto_v2.py` avise si falta la grilla y diga el comando pymupdf exacto para recortarla.
2. **Paso 3b, `remapear_hermana.py`:**
   - **Mapa con identidad:** un número que se queda igual (`"8":"8"`) da «error: 8 quedan sin mapa y chocan». Lo pasé por `x8` y lo renombré en mi script. *Propuesta:* aceptar la identidad.
   - **No copia el lado repetido:** la NMAX tiene dos barras con números distintos y la Honda dibuja los internos de una sola. *Propuesta:* una opción `--espejo <eje x> --mapa-lado '{…}'` que duplique piezas, fichas y enlaces del otro lado.
3. **`--rapido`, control «¿remapeado dos veces?» (`mas_controles.py` ~791): falso positivo.**
   - Compara el texto del enlace con el de la hermana, así que cada enlace legítimo de la barra derecha y los nuevos («seguro», «tapón», «guardapolvo») dieron error: más de 10.
   - Lo esquivé cambiando el texto («retén derecho», «tapón del eje»).
   - *Propuesta:* saltar los enlaces cuyo número es de una pieza sin equivalente en el mapa, o que estén en fichas nuevas.
4. **Rastros de la hermana que `--rapido` no ve:** `visor.sub` («Fig. F-8 · 19 números») y `pie` («horquilla CB 125F»). Los vi en la previa. *Propuesta:* incluir `visor` y `pie` en la búsqueda de rastros.
5. **Lo que la máquina podría atrapar antes de la revisora** (los 9 graves eran de este tipo):
   - nombres de piezas de la hermana que no existen en el catálogo nuevo («asiento», «o-ring» donde el catálogo dice GASKET);
   - frases de equipamiento ajeno («tija de arriba»).
   *Propuesta:* que `remapear_hermana.py` liste las palabras de la ficha de la hermana que no aparecen en la descripción del catálogo nuevo (O-RING vs GASKET).
6. **`anexo-desarme.md` / seguridad:** hace falta una regla por moto: en scooters, el gato central no levanta la rueda delantera.
7. **`aplicar_hallazgos.py`:** dos hallazgos sobre el mismo campo (`pasos.0.t`) aplicaron solo uno y dejaron el otro «a mano» sin decir por qué.
