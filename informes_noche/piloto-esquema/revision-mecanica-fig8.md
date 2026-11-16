# Revisión mecánica: fig. 8 de la NMAX 155 BBE4, «Admisión y filtro de aire»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig8.json`: 37 números, 9 pasos con `sujeta`, «Cómo funciona» de 5 pasos, 3 cadenas, «Cuándo» y las fichas. Lo comparé con `garaje/intervalos/yamaha_nmax_155.json` (filtro cada 15.000 km, de papel con aceite) y con `autocontrol-mecanico.md`. Solo califico lo mecánico.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Los 37 nombres y las cantidades son coherentes con la lámina (por ejemplo, 9 tornillos de la tapa y 2 O-rings del inyector). `sujeta` es correcto: la abrazadera 33 sujeta la unión 22, el tornillo 10 sujeta el inyector, los tornillos 31 sujetan la caja con sus bujes y cauchos, y los tornillos 3 sujetan el múltiple y su soporte. |
| 2 | Exactitud mecánica | **4** | El motor de ralentí como paso de aire al lado de la mariposa, los pulsos del inyector, el respiradero que lleva vapores a la caja y el drenaje están bien explicados. El filtro es de papel con aceite y «no se sopla ni se lava», como dice el plan. **Hay un error:** la mezcla «rica» con el filtro tapado (cambio 1). |
| 3 | Pedagogía | **5** | Los 5 pasos de «Cómo funciona» son claros, y la cadena «Drenaje lleno» es muy buena para el taller. |
| 4 | Congruencia | **4** | El filtro cada 15.000 km es igual al plan y al manual, marcado «Seguro». **Pero la ficha 22 se contradice**: la causa ya dice «aire sin filtrar», mientras el síntoma sigue siendo de aire falso (cambio 2). |
| 6 | Reglas | **5** | No hay torques inventados: van «sin dato» o remiten al manual de servicio. La práctica de taller está marcada como «Aproximado». El 19 % de certeza es bajo, pero honesto: se sabe qué es manual y qué no. |

**Promedio: 4,4. Visto bueno: NO, por ahora.** Con los cambios 1 a 3, la nota sube a 4,8.

## Confirmaciones pedidas
- **Unión 22: es correcto, y no es aire falso.** La unión está **antes** de la mariposa. La NMAX mide la carga con la mariposa y la presión del múltiple, así que el aire que entra por una grieta en la unión igual queda medido y no empobrece la mezcla. El daño es otro: el polvo entra sin filtrar y raya el cilindro y los anillos.
  - En cambio, el aire falso de los empaques 2 y 11 y del O-ring 6 está bien: van **después** de la mariposa.
- **Orden del desarme y `sujeta`:** son correctos. Tapa → filtro → mangueras → unión → caja → inyector → cuerpo → motor de ralentí → múltiple. Cada pieza sale después de lo que la sujeta.
- **Torques:** todos van «sin dato» o remiten al manual de servicio. ✔

## Cambios pedidos
1. **Error: la mezcla «rica» con el filtro tapado** (cadena «Filtro sin cambiar», `nmax-fig8.json:3096`). Eso es lógica de carburador. En la NMAX, con inyección, el computador mide la presión del múltiple: si entra menos aire, manda menos gasolina.
   - Proponer: **«Llega menos aire y el computador da menos gasolina: la moto pierde fuerza y tienes que acelerar más»**.
   - Revisar las otras 4 apariciones de «rica» y el «gasta más» de la ficha 23 y del paso 5 de «Cómo funciona»: que digan «pierde fuerza; puede gastar algo más porque aceleras más», no que la mezcla se enriquece.
2. **Ficha 22: el síntoma contradice la causa** (`:2387`). «Se oye una succión o un silbido cerca de la caja al acelerar» es síntoma de aire falso. Delante de la mariposa casi no suena.
   - Cambiarlo por **«La grieta se ve al doblar los pliegues»** y **«Hay polvo en la boca del cuerpo de aceleración»** (este último ya está).
3. **Paso 6, inyector: falta el aviso de incendio** (`:1325`). Se dice «gasolina a presión», pero falta cómo trabajar con ella:
   - motor frío y lejos de chispas o cigarrillos;
   - un trapo para recoger la gasolina que sale al soltar el tubo, porque queda presión aunque la moto esté apagada;
   - al armar, revisar que no gotee antes de prender.
4. **Verificar en el cuadro del manual B6Y4** si aparece el **tubo de comprobación del filtro** (el drenaje 26 y 27) con su propio intervalo. En muchos Yamaha aparece como «limpiar». Si está, la fila «Vaciar el tapón» pasa a «Seguro» con su intervalo; si no, se queda como práctica de taller.
5. **Menor:** el paso 1 dice «Baja la tapa derecho», que se puede leer como el lado derecho. Mejor «recta».

## Verificación (16-nov-2026, después de las correcciones)

| # | Punto | Estado |
|---|---|---|
| 1 | Ya no dice «mezcla rica» | ✔ La cadena, la ficha 23 y el paso 5 de «Cómo funciona» dicen ahora «el computador manda menos gasolina; pierde fuerza y tienes que acelerar más». Las 4 veces que aparece «rica» son dentro de otras palabras («eléctrica», «lubricante»). |
| 2 | Ficha 22 | ✔ Síntomas: grietas en los pliegues al doblarlos y polvo en la boca del cuerpo, después del filtro. Los «silbidos» que quedan son de los empaques que van después de la mariposa, y esos sí son aire falso. |
| 3 | Inyector (paso 6) | ✔ Motor frío, lejos de chispas, llamas y cigarrillos; trapo para la gasolina que sale con presión aunque la moto esté apagada; y al armar, poner el contacto sin prender y revisar que no gotee antes de arrancar. |
| 4 | Tubo de drenaje | ✔ Revisar a los 1.000 km y luego cada 6.000 km o 6 meses, marcado «Seguro» y citando el cuadro del manual (p. 9-4) y la sección de limpieza. La ficha 27 coincide. |
| 5 | «Recta» | ✔ |

**Nota final: 4,8** (fidelidad 4 · exactitud 5 · pedagogía 5 · congruencia 5 · reglas 5). **Visto bueno: SÍ.**
