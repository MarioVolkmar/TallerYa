# Relevo: rehacer los «Cómo funciona» (16-nov-2026, 10:30)

Pedido del usuario (vía Auxiliares): llevar los «Cómo funciona» al nivel de la CVT (nota 5: corte, rpm, varios cambios por paso). Calificación de ux-piloto en `informes_noche/piloto-esquema/revision-como-funciona.md`. **Va después de los pedidos del motor** (`informes_noche/relevos/motor-pedidos-usuario.md`), en serie. Cronometrar cada uno como mejora de su lámina: `metricas.py inicio|fin <lamina> correcciones`.

## Criterio mínimo (ya está en la skill `hacer-lamina`, paso 4)
Al menos 3 piezas reconocibles (no cajas); un corte o transparencia; cada paso cambia algo visible que corresponde al texto; un indicador físico que cambia, cuando aplica; etiquetas sin montarse y de 12 px o más (en el SVG, ~20 unidades: `#fn .esq-fn-et{font-size:20px}`); pasos de 250 caracteres como máximo.

## Dónde está cada uno
El SVG va en `FN_SVG` y la animación en `fnAplicar(s,$)` de `informes_noche/piloto-esquema/motor/datos/<lamina>-arte.js`. Los pasos (texto + estado `s`) van en `funciona.pasos` del JSON. Reglas del celular (`#fnCorte`, `vbCelular`, `data-xm`/`data-ym`) en `.claude/skills/hacer-lamina/anexo-formato.md`. Referencia de calidad: la CVT (`datos/nmax-fig12-arte.js`).

## En orden
1. **Fig. 8, admisión (nota 2):** caja con filtro plisado, cuerpo de aceleración en corte con la mariposa que gira, inyector reconocible rociando un cono. Animar: acelerar → más aire y más gasolina; filtro tapado → menos aire. Indicadores de % de acelerador, flujo y rpm. Etiquetas separadas.
2. **Fig. 10, cárter (2):** corte con el aceite y la varilla con mín./máx. Animar cómo se mide (sacar, limpiar, meter, leer), la transmisión final salpicando y el retén en corte. Indicador de nivel en litros (0,90 L motor; 0,10 L transmisión final).
3. **Fig. 7, aceite (2,5):** bomba trocoidal en corte girando, tamiz con partículas, cigüeñal y levas reales. Indicadores de presión (sube con las rpm) y del color del aceite (se oscurece con los km).
   → Al terminar estos 3, mensaje a Auxiliares.
4. **Fig. 11, tapa (2,5):** filtro de espuma en corte con polvo; la polea con aletas aspirando aire por la rejilla para enfriar la correa. Indicadores de °C de la correa y % de flujo.
5. **Fig. 1, culata (3,5):** los 4 tiempos animados (pistón, válvulas y chispa, con colores) con un indicador de ángulo del cigüeñal (0-720°) o del tiempo, y volumen como en el dibujo (degradados). Hoy: 6 pasos con pistón, válvulas, chispa, gas por color y agua; las etiquetas ya van a 20 unidades.
   → Al final, mensaje a Auxiliares.

## Ya hecho en esta sesión
- Fig. 24: la etiqueta del esquema dice «Puño izquierdo» (antes «Puño derecho»); archivo único rearmado. El dibujo de la manigueta no se espejó: revisar si hace falta.
- Letra mínima de 12 px en el esquema a 1280: la fig. 1 se arregló en su arte. El arreglo general del motor está en el relevo del motor (punto «A tener en cuenta»).

## Al medir
- `autocontrol.py <lamina> --antes` antes de corregir: el validador avisa con «regresión:» si se pierde una palabra de seguridad.
- Cada lámina: `--rapido` hasta 0 errores, `--previa` para mirar, y medición final con `--captura` y `--ojo`; después, `armar_un_archivo.py`.
- En los heredocs de Bash de esta máquina, `\\` llega como `\`: los parches con regex van en un archivo escrito con Write.

## Estado al 16-nov-2026 (relevo de la creadora, tras el trabajo 1)
- **Trabajo 1 (pedidos del motor) terminado**: ver la nota de arriba en `informes_noche/piloto-esquema/cambios.md`. El relevo `motor-pedidos-usuario.md` queda cerrado.
- **Trabajo 2: nada empezado.** Se empieza por la fig. 8 en una sesión limpia (la creadora pasó del 50 % de contexto).
- Letra: el motor ya pone `.esq-fn-et` a 16 px (escritorio) y 22 px (celular): con eso las 9 dan ≥ 12 px. Al rehacer, una etiqueta nueva sin tamaño propio ya cumple; no hace falta `font-size:20px` salvo que el dibujo lo pida (la fig. 1 lo tiene en su arte).
- La fig. 8 tiene hoy etiquetas montadas en «Cómo funciona» («Mariposa y ral…» / «Inyector», a 1280 y 360): se arregla al rehacerla.
- La fig. 26 (fuera de este trabajo) da bloqueante por un paso de «Cómo funciona» de 272 caracteres: tarea de contenido.
- Para medir rápido la letra y los solapes de las 9 sin `medir_lamina`: un iframe por página (1280×800 y 360×740), pestaña «Cómo funciona», recorrer los pasos y comparar `getBoundingClientRect` de los `text` visibles (así se hizo en el trabajo 1).
- Capturas a escala 0,5 con Chrome sin ventana: `informes_noche/piloto-esquema/capturas-motor-pedidos/capturas.py <trabajos.json>` (ejemplo en `trabajos1.json`; servidor estático en el puerto 8010). Para «Cómo funciona»: `js` que haga `document.getElementById('t-funciona').click()` y avance al paso más rico, y `clip` `#p-funciona`.

## Estado al 16-nov-2026, 11:25: trabajo 2 terminado
- Fig. 8, 10, 7, 11 y 1 rehechas y la fig. 26 acortada (ver la nota de arriba en `piloto-esquema/cambios.md`). Las seis: «mínimo CUMPLE», sin bloqueantes, validador en 0 y archivo único rearmado. Sin commit.
- Faltan las notas a ojo y las revisiones (mecánica y UX). Las cifras de presión (bar) y temperatura de la correa (°C) son aproximadas y se marcan «aprox.».
