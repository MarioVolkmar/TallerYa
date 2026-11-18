# Prueba de modelo: AKT NKD 125 · freno delantero (fig. F-5)

**17-nov-2026, 12:38-12:54.** Lámina hecha con la skill `hacer-lamina` sin editarla.

## ⚠ Esta prueba no corrió en Fable
El encargo decía que la sesión corría en Fable 5.2. Pero la sesión reportó el modelo **Claude Opus 5.5** (`claude-opus-5-5`), y `get_usage` dejó el uso semanal de Fable en **0 %** al empezar y al terminar. Así que esto es **otra corrida en Opus**, no una comparación entre modelos. Para medir Fable de verdad, hay que abrir una sesión nueva con Fable elegido en el selector de modelo y repetir la prueba (sugerencia: otra figura con hermana de la misma numeración).

## Resultado
- Página `motor/nkd-freno.html`, archivo único `motor/prueba-nkd-freno.html`; datos `motor/datos/nkd-freno.json` y `-arte.js`.
- Validador **0 errores, 0 avisos**; medición final **sin bloqueantes, medible 4,88** (criterios 6: 5 · 8: 4,7 · 9: 5 · 10: 5 · 11: 4,8 · 12: 4,8).
- La F-5 sí sirve: 9 refs (kit 1 = sistema completo; bomba CBS, manigueta, interruptor, manguera, pastillas, cáliper completo, 2 tornillos de unión, cable del CBS de 127 cm). El disco está en la F-6 y va de contexto.
- Hermana: `crypton-freno` remapeada (`remapear_hermana.py`) para el cáliper, las pastillas, el disco y «Cómo funciona». Bomba, manigueta e interruptor salieron de `nmax-fig26`. El cable del CBS se dibujó nuevo.

## Tabla contra las 5 láminas de anoche (Opus)
| lámina | hermana | tiempo con revisión | mediciones | tokens creación / revisora | medible | revisora mec. / UX (antes de corregir) | graves |
|---|---|---|---|---|---|---|---|
| Crypton · freno delantero | nmax-fig22 | 13 min | 1 | ~175 k / 104 k | 4,80 | 3,9 / 3,6 | 3 (de 7) |
| NKD · rueda trasera | no | 14 min | 2 | ~98 k / 91 k | 4,88 | 4,0 / 4,0 | 4 (de 13) |
| NMAX · horquilla | cb125f-horquilla | 13 (16 de reloj) | 1 | ~98 k / 108 k | 4,73 | 3,5 / 3,9 | 9 (de 15) |
| Boxer · carburador | no | 23 min | 4 | ~128 k / 91 k | 4,82 | 4,0 / 4,3 | 5 (de 15) |
| CB 125F · susp. trasera | no | 13 min | 2 | ~140 k / 96 k | 4,88 | 4,0 / 4,3 | 3 (de 15) |
| **NKD · freno delantero (hoy, Opus 5.5)** | crypton-freno + nmax-fig26 | **16 min de reloj** (15 por fases) | **1** | **~162 k / 89 k** | **4,88** | **4,2 / 4,4** | **4 (de 13)** |

Tiempo por fase (real / meta): catálogo 2,0/1,5 · dibujo + contenido **9,0/4 (CORTE)** · validación 1,0 · mediciones 3,0/2,5 (incluye la previa) · revisión (correcciones) 1,0/1,5 · espera de la revisora 2 (aparte).
Tokens de creación: estimados como el contexto de mensajes al terminar (220 k usados − ~58 k fijos). Revisora: 89.410 (dato del subagente).

## Lectura
- **Mejor que anoche:** revisora 4,2 / 4,4 (la más alta de la serie), una sola medición, revisión en 1 min y medible igual al tope (4,88).
- **Peor:** el tiempo. Dibujo + contenido tomó 9 min porque la hermana sugerida tiene otra forma: es un cáliper desarmado (16 refs), mientras la F-5 es el sistema entero con el cáliper completo. Quedó poco de ella; hubo que juntar dos láminas, dibujar el cable y escribir casi todas las fichas de cero.
- **Graves de la revisora (4):** todos de seguridad y redacción del desarme: holgura del cable del CBS al armar, bombear la manigueta después de cambiar pastillas, en qué caso aplica el aviso «no aprietes con el cáliper fuera» y que el líquido no gotee en las pastillas. Se aplicaron los 13 hallazgos.
- Las notas a ojo (4,0) quedaron bajo la línea base (4,5). Fueron conservadoras: no hubo una segunda mirada.

## Mejoras para la skill (sin aplicar)
1. **Elegir la hermana por cobertura, no por sistema.** `remapear_hermana.py` podría imprimir «% de piezas de la figura nueva que la hermana cubre» (aquí: 2 de 8). Con menos del 50 %, conviene combinar hermanas o partir de la biblioteca.
2. **Combinar dos hermanas.** Traer funciones de arte de una segunda lámina (bomba de `nmax-fig26`) se hizo con un script a mano. Un `--arte-extra <lamina>:<funciones>` ahorraría ~2 min.
3. **`plantillas_ficha.py`: plantillas que faltan**: bomba de freno, manigueta, interruptor y cable del CBS.
4. **El validador pide el intervalo del líquido (2 años) en manigueta y tornillos de unión.** Toma «kit o sello del freno hidráulico» de forma demasiado amplia: a la manigueta no le corresponde.
5. **Manual escaneado:** `buscar_manual.py --indice` podría decirlo de una vez y sugerir `garaje/intervalos` sin hacer la segunda búsqueda.
6. En Windows con Git Bash, un heredoc largo con `«»` y comillas falló («unexpected EOF»): para scripts largos, mejor la herramienta Write.

## Pendientes de la lámina
Torques (sin dato, manual de servicio AKT) · tipo de líquido y plazos (manual escaneado; no hay tareas de freno en `garaje/intervalos/akt_nkd_125.json`) · contenido exacto del kit ref. 1 · ajuste del cable del CBS · sin 3D propio para la bomba ni el cáliper (solo el tornillo de unión, de la biblioteca).
