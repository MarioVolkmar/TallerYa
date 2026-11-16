# Relevo: creadora de esquemas del motor (16-nov-2026, tarde)

## Hecho (detalle en cambios.md, entrada «Desarme general por bloques…»)
- A) Desarme general por bloques (`esquema.js`: SEP, `calcularOFF`, `sumaTodo(k,dentro)`, `encuadreTodo`) + control de solape (`motor/medir_solape.js`, en `medir_lamina.py`; `--solape` rápido con `--captura-desarme/--captura-trans`). Las 9 ≤ 9 % salvo fig. 26 (11 %, aviso). Ojo: `separar_numeros.py` también mueve desplazamientos de piezas: después de separar, volver a correr `--solape`.
- B) Interruptor «Transparente» (`#iTrans`, junto a «Números»; en el celular solo ícono) + `carcasas` en fig. 1, 7, 8, 10, 11.
- Retoques de la revisora (fig. 1 ideal + cruce, fig. 8 paso 6, fig. 11 «aprox.») y correa de la CVT con temporizador.
- Firmas del armado idénticas (salvo `guiasG`, temporización); validador 0 errores en las 9; archivos únicos rearmados.
- Helper para mover piezas en el desarme: scratchpad `mover.py` (suma dx,dy al último paso de la pieza); si no está, es 10 líneas.

## Bloqueantes medidos que ya existían (son las correcciones de UX pendientes)
- Fig. 12: paso de «Cómo funciona» de 341 caracteres. Fig. 22 y 24: paso de 397 caracteres y paso 4 sin cambio visible. Fig. 7: marcas de grupo de 43 px a 1440.

## Pendiente, en este orden (pedidos de Auxiliares)
1. Correcciones UX aprobadas (`revision-ux-como-funciona-v2.md`): fig. 22/24 a 390 px separar «Pastillas» de «Rueda», acortar el paso de 397, paso 4 con cambio visible; CVT acortar el paso de 341; fig. 26 sacar «Manguera» de debajo del cáliper (indicador de presión opcional); fig. 7 marcas de 43 a 44 px. No tocar la Boxer (sesión lamina-boxer).
2. Panel izquierdo al elegir en el catálogo derecho (motor, todas las láminas; ver `criterios-del-usuario.md`): al tocar grupo o pieza en la lista, la izquierda pasa a «Piezas», entra al grupo, resalta la pieza como si la tocara en el dibujo y la centra sin que la tape la cabecera; al revés, tocar en el dibujo despliega y centra la pieza en la lista. Probar a 1280 y 390 en CVT, fig. 22, fig. 26, culata y `motor/prueba-boxer-embrague.html`; rearmar archivos únicos; agregarlo a los criterios.
   - El mensaje anterior pedía, para «Si falla» y «Cuándo», quedarse en la pestaña y filtrar («Ver todo» chico, línea «Esta pieza no tiene cadenas de falla propias»). El último pedido del usuario dice que SIEMPRE cambie a «Piezas»: confirmar con Auxiliares cuál vale antes de hacerlo (parecen contradecirse).
3. Opciones UX v3 aprobadas (7, 8, 9, 12 de `propuesta-ux-v3.md`): semáforo `rodar` ("sigue"|"pronto"|"no") por pieza junto al resumen; «¿Lo puedes hacer tú?» con herramientas y tiempo (campo nuevo, solo con dificultad «Lo puedes hacer tú»); glosario al tocar (subrayado punteado una vez por ficha, fuente `garaje/despiece_glosario.py`); recordar la última pieza vista (localStorage con try/catch). Proponer valores en las 9 y listarlos en el mensaje final para la revisora.
- Cada lámina: `autocontrol.py <lamina> --antes` antes de tocarla. Sin commit. Un solo mensaje a Auxiliares al terminar.

## Hecho la noche del 16-nov (sesión de retoma)
- Los puntos 1, 2 y 3 del pendiente están hechos; el detalle, en `cambios.md` («Correcciones UX, catálogo ↔ panel izquierdo…»). Para «Si falla» y «Cuándo» se aplicó la **mezcla**, que eligió el usuario.
- Queda para la revisora: los valores de `rodar` y `hazlo` (propuestos con reglas por nombre) y las definiciones «+» del glosario en `esquema.js`.
- Ayudantes en el scratchpad de la sesión (se pueden perder): `evaljs.py` (abre una página en Chrome sin ventana a un ancho y evalúa JS), `prueba_catalogo.js`, `prueba_v3.js` y `fn_choques.js`.
