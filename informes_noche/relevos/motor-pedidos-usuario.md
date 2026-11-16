# Relevo: pedidos del usuario para el motor del esquema (16-nov-2026, 10:20)

Pedidos del usuario (vía Auxiliares) para `informes_noche/piloto-esquema/motor/esquema.js` y `esquema.css`; valen para las 9 láminas. Capturas de referencia: `C:\Users\volkm\AppData\Local\Temp\claude\7ac1c0565177d901\0ebba277-a9d1-46bf-b892-ba006053b12e\images\15.png` a `20.png`, `22.png` y `23.png`. **Hecho (16-nov-2026): ver `piloto-esquema/cambios.md`.**

## Antes de tocar el motor
`firma_lamina.py` de las 9 páginas (`cvt freno bomba-freno admision freno-trasero aceite carter tapa-transmision culata`.html) con `--guardar <scratchpad>/firmas.json`; al final `--comparar`. Aquí las firmas pueden cambiar, pero solo por estos pedidos.

## Pedidos
1. **Bug:** se ve el marcado crudo `[[n|texto]]` fuera de la ficha («Cómo funciona», pasos, cadenas, «Cuándo»; fig. 7, imagen 19). Renderizarlo en todos los textos como el enlace sutil de la ficha (lleva a la pieza). El validador avisa si queda `[[` sin renderizar en la página.
2. Con «Números» activado, las píldoras de grupo tapan los números (fig. 26, imagen 16): en ese modo, píldoras en forma mínima (punto o etiqueta corta) o apartadas, y ningún número debajo de una píldora.
3. «Piezas relacionadas» (imagen 17): chips del mismo alto y en una línea, con nombre corto («Perno hueco (del.)») y el completo en title/aria-label, o una rejilla de ancho igual con el texto recortado.
4. «Fuentes» (imagen 18): un chip chico con ícono de libro o documento, discreto.
5. Vista general: opción de desarmar todo el sistema a la vez, con la misma animación y ◀ ▶ por grupo o por paso. Al volver, se arma.
6. Vista general de la fig. 7 (imagen 20): el encuadre debe ceñirse a las piezas, con el contexto recortado.
7. Botones ‹ Anterior | Lista | Siguiente › de la ficha (imágenes 22-23): más finos (minúscula o versalitas, más chicos), área de toque de 44 px invisible; «anterior» desactivado se nota pero no estorba.
8. Elegir una pieza (lista o enlace) desde «Cómo funciona», «Si falla» o «Cuándo» cambia sola a «Piezas» y la muestra en el dibujo.
9. Píldora de grupo con el cursor encima: la misma píldora se alarga con el nombre largo («Caja» → «Caja del filtro»), sin una viñeta nueva al lado.
10. Dentro de un grupo, las píldoras de tornillería («Grapa (1)») tapan el dibujo: al borde del encuadre o a zonas libres, con una línea guía fina hasta su punto, más chicas y con fondo semitransparente.
11. (De la revisión UX de la fig. 1) Línea guía de la píldora de grupo hasta su capa, cuando la píldora se pone a mano con `marca` en el borde visible.

## Al terminar
Validar las 9 (`autocontrol.py <lamina> --rapido`), rearmar los archivos únicos (`armar_un_archivo.py`) y sacar 3 capturas a escala 0,5: modo Números en la fig. 26, una ficha con relacionadas, fuentes y los botones nuevos, y la vista general desarmada. Un solo mensaje a Auxiliares.

## A tener en cuenta
- `medir_lamina.py` tiene una regla nueva: la letra mínima de «Cómo funciona» debe ser ≥ 12 px (la fig. 1 daba 9,9 px a 1280 y se arregló con `#fn .esq-fn-et{font-size:20px}` en su arte). Las otras 8 pueden dar ese bloqueante: medirlas.
- El validador ahora avisa por pasos de más de 300 caracteres: figs. 7 (paso 3), 8 (6), 12 (15), 22 (14), 24 (14) y 26 (2, 8 y 17). Acortarlos es tarea de contenido, no del motor.
- En los heredocs de Bash de esta máquina, `\\` llega como `\`: los parches con regex van en un archivo escrito con Write, no en un heredoc.
