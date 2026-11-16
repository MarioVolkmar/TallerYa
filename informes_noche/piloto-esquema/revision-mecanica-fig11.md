# Revisión mecánica: fig. 11 de la NMAX 155 BBE4, «Tapa de la transmisión y filtro de la correa»

Revisora · 16-nov-2026 · Revisé `motor/datos/nmax-fig11.json`: 23 números, 10 pasos con `sujeta`, «Cómo funciona» de 6 pasos, 3 cadenas, «Cuándo» y las fichas. Lo comparé con `yamaha_nmax_155.json` (filtro de la caja cada 6.000 km; correa cada 18.000 km) y con el autocontrol. Solo califico lo mecánico.

## Puntajes

| # | Criterio | Nota | Evidencia breve |
|---|---|---|---|
| 1 | Fidelidad | **4** | Nombres y cantidades del catálogo: 10 tornillos de la tapa de aluminio, 6 de la exterior, 10 espumas. `sujeta` es correcto: la tapa exterior lleva el filtro, sus sellos y las espumas, y los tornillos 4 sujetan la tapa 1, que lleva el empaque y el pasador. La posición de las espumas es aproximada. |
| 2 | Exactitud mecánica | **5** | El aire lo aspiran las aletas de la polea fija del variador, pasa por la esponja aceitada y sale por atrás. Con el filtro sucio, la correa se calienta y patina. El respiradero y el tubo colector están bien explicados. Ficha 11: disolvente y nunca gasolina, **exprimir sin retorcer**, aceite para filtros de esponja, y que quede húmeda sin gotear. Es exactamente el procedimiento de Yamaha. |
| 3 | Pedagogía | **5** | Los 6 pasos son claros. La cadena «Espuma suelta que tapa el filtro» es un caso real de taller. |
| 4 | Congruencia | **5** | Filtro cada 6.000 km (pp. 9-4, 9-18 y 9-19), correa cada 18.000 km y tubo colector según p. 9-18: igual que el plan. El empaque está marcado como práctica de taller. |
| 6 | Reglas | **5** | Sin torques inventados: el paso 10 remite al manual de servicio. La tecnología es la correcta (CVT en seco, sin «rica» ni carburador). El trabajo con disolventes avisa del riesgo de incendio. |

**Promedio: 4,8. Visto bueno: SÍ.** No hay errores mecánicos.

## Retoques que no bloquean
1. **Paso 4** (`nmax-fig11.json:812`): resume «se lava con disolvente y se aceita». Conviene agregar **«exprímela sin retorcer»**, como dice la ficha 11, porque retorcerla es la forma más común de romperla.
2. **Paso 8** (`:860`): «Aflójalos en cruz, de afuera hacia adentro». En una tapa con los tornillos en el borde, «de afuera hacia adentro» no tiene sentido. Basta con **«aflójalos en cruz, un poco cada uno»**.
3. **Ficha 1, síntoma «aceite… por la junta»**: la caja de la correa es seca. Si sale aceite ahí, viene de un retén (del cigüeñal o de la transmisión final), no de la tapa. Conviene decirlo: **«Si ves aceite, revisa los retenes: la caja debe estar seca»**.
