# Preferencias del usuario (segunda capa, sobre la congruencia con la guía)

Gustos que el usuario ya expresó al corregir entregas. Se revisan **después** de la regla 1 (congruencia con
[anexo-guia.md](anexo-guia.md)) y **antes** del resto de la lista. Cada regla: qué, antes → después, de dónde salió.

**Cómo se aprende:** cuando el usuario corrija un detalle visual, la sesión que lo arregla agrega aquí la regla
(o amplía el ejemplo de una que ya existe: **no duplicar**), con fecha y página. Formato:
`N. **Regla corta.** Antes: … → Después: … _(fecha · página)_`. Si la regla contradice otra, gana la más reciente y la
vieja se borra. Luego se copia el archivo al respaldo (`~/.claude/skills_respaldo/tallerya/revisar-ux/`).

## Forma y componentes
1. **Nada punteado.** Ni recuadros, ni avisos, ni separadores con borde punteado; solo las zonas para subir archivos.
   Antes: aviso «Mi ruta · tu jornada…» con borde punteado en `/garaje/` → Después: se quitó; una chapa pequeña «Trabajo» en la tarjeta. _(19-nov · garaje)_
2. **Nada de enlaces subrayados sueltos.** Una acción es un botón secundario o un chip; el subrayado solo dentro de una frase,
   y nunca enlaces naranjas que rompan el renglón. Antes: «Ajustes», «ver», «Gastos: Gastos y consumo.» →
   Después: botón con ícono de engranaje «Ajustes», botón «Ver gastos y consumo →». _(16 y 19-nov · Mi ruta, despiece)_
3. **Los botones respiran.** El texto nunca toca el borde ni se corta; si no cabe, texto más corto o el botón a todo
   el ancho en el celular. Antes: «Cerrar jornada» pegado al borde → Después: relleno, interlineado y los dos botones apilados a 375 px. _(19-nov · franja Moto de trabajo)_
4. **Los controles van dentro de su tarjeta.** Interruptores, «Eliminar» y similares viven en la tarjeta a la que
   pertenecen (barra de edición abajo, separada por una línea fina), nunca sueltos debajo. Antes: «La uso para trabajar»
   fuera de la tarjeta → Después: dentro, a la izquierda, con «Eliminar» a la derecha a la misma altura. _(19-nov · garaje, modo Editar)_
5. **Lo que sobresale de una tarjeta acompaña su hover.** Chapas, sellos y etiquetas pegadas al borde se mueven con
   la tarjeta (mismo desplazamiento −2/−3 px y 0,2 s), también con foco. Antes: la chapa «Trabajo» quieta mientras la
   tarjeta subía → Después: se elevan juntas. _(19-nov · garaje)_
6. **Nada tapa nada.** Botones flotantes, WhatsApp, Chispa o la barra inferior no se montan sobre textos ni dibujos.
   Antes: el horario de la tarjeta de taller tapado por el botón de WhatsApp → Después: espacio reservado para el botón. _(19-nov · tarjeta de taller)_
7. **Pequeño y discreto antes que grande.** Píldoras, botones compactos, nada de filas de botones grandes ni barras
   fijas toscas en el celular. Antes: botones grandes «Pedir repuesto» y «Talleres», barra fija «Ver ficha» → Después: botones compactos en la ficha. _(15/16-nov · despiece)_

## Jerarquía
8. **El protagonista de cada página va primero.** En el detalle de la moto manda la moto (estado, agenda, dibujo); lo
   secundario (Ruta, plan de trabajo, promociones) va discreto y no de primero. Antes: tarjeta grande de Ruta arriba
   del detalle → Después: franja compacta dentro de la agenda. _(19-nov · detalle de moto)_
9. **Los sellos muestran solo lo positivo.** «Verificado por TallerYa» con lo que sí se revisó; nunca una lista de lo
   que falta, y sin verificación no hay sello. Antes: sección «02 Lo que revisó TallerYa» con guiones que parecían
   fallas → Después: sello junto al nombre con un desplegable «Identidad confirmada · Experiencia revisada». _(18-nov · ficha del mecánico)_
10. **Avisos legales discretos.** Una línea gris pequeña bajo las acciones, con «Más info» plegable; nunca una caja
    amarilla. Antes: caja amarilla en «Servicios» → Después: «TallerYa conecta; el acuerdo y el pago son con el mecánico. Más info». _(18-nov · ficha del mecánico)_
11. **Poco ruido.** Sin leyendas aparte, sin bloques de «Fuentes y certeza», sin sopas de números; la certeza va
    dentro del texto, discreta. _(15/16-nov · despiece)_

## Textos
12. **Sin instrucciones obvias.** Si el componente se entiende solo, no se explica. Antes: «Toca uno para pedir la visita»
    → Después: chips con una flecha «›» que se mueve con el hover y `title` «Solicitar visita: frenos». _(18-nov · ficha del mecánico)_
13. **Mayúscula inicial siempre** en etiquetas, chips, botones y frases. Antes: «escáner básico, multímetro» → Después: «Escáner básico, Multímetro». _(18-nov · ficha del mecánico)_
14. **El nombre de la sección describe todo su contenido.** Si una sección mezcla cosas, se renombra o se separa.
    Antes: «Papeles de tu moto» con el diagnóstico adentro → Después: nombre que cubre lo que hay (o el diagnóstico en su sección). _(19-nov · garaje)_
15. **Un dato que falta es una acción, no un «—».** Antes: «—» en pico y placa sin placa → Después: «Agrega la placa
    para ver tu pico y placa de hoy y mañana» + botón «Agregar placa». _(19-nov · franja Moto de trabajo)_
16. **De tú, corto y práctico**, sin jerga del catálogo ni «(N)» en el texto. _(15/16-nov · despiece)_
