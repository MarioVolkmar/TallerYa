# Revisión UX: fig. 10 «Cárter y tapones del aceite» (`motor/carter.html`) y encuadre de la fig. 7

Revisora UX · 16-nov-2026 (08:39–08:43). Medí con `medir_lamina.py` en los 6 anchos (rúbrica v3). Revisé a ojo con dos capturas: vista general a 1280 y grupo «Aceite del motor» con hoja a 390. Medí el encuadre de cada grupo frente al tamaño de sus piezas.

## Fig. 10: aprueba
| Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Bloqueantes |
|---|---|---|---|
| 4,5 · 4,7 · 5 · 5 · 4,8 · 4,8 = **4,80** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,65** | ninguno |

**Medidas:**
- 6 grupos con marcas de 46 px, sin fallas ni solapes.
- Dibujo completo en los 6 anchos. «Desarmar» queda a la vista al entrar a un grupo, con desarme de 2,7 s.
- Hoja inferior al 12 %, sin tapar la pieza.
- 19 de 20 piezas tienen 24 px o más; el respiradero 29 queda en 23 px.
- «¿Se repara?» a 0,71 pantallas del inicio de la ficha.
- Sin errores. El 3D abre en la varilla del aceite.
- Avisos que no bajan la nota: con el grupo armado, asoman bordes de la 10 (Aceite del motor) y la 30 (Tapa 2) que no responden.

**A ojo:**
- El cárter va en gris claro, con volumen y detalle (nervios, tapas, retenes). **No es una mancha:** se lee sin las píldoras.
- Seis píldoras chicas bien repartidas.
- **Lenguaje:** «Tapa 2» suena a catálogo. Para el motero conviene «Tapa del respiradero» o «Tapa del lado del variador»; la lista ya dice «Tapa 2 del cárter y respiradero». «Tapa de atrás» se entiende.

## La fig. 7 en el celular: el grupo chico **no** se ve más cerca
Bajar `minW` de 380 a 220 no cambió nada: el resorte 5 sigue en 20 px y el tapón se ve diminuto. La causa no es el mínimo, es **qué se encuadra**:

| Lámina · grupo | Piezas armadas (unidades del dibujo) | Encuadre del grupo | Por qué |
|---|---|---|---|
| Fig. 7 · drenaje | 68 × 168 | **631 × 490** | el encuadre suma las posiciones desarmadas, que se alejan mucho |
| Fig. 10 · Aceite del motor | 82 × 398 | **852 × 663** | la varilla (arriba) y el perno de drenaje (abajo) están en extremos opuestos |
| Fig. 10 · Transmisión final | 112 × 243 | 621 × 483 | grupo alto en un lienzo apaisado, más el desarme |
| Fig. 7 · bomba (para comparar) | 155 × 131 | 351 × 273 | bien |

## Qué corregir
1. **Motor: encuadrar según el estado del grupo.** Al entrar, encuadrar solo las piezas armadas. Al tocar «Desarmar», ampliar con una animación hasta abarcar lo desarmado, y volver al armar.
   - En el drenaje de la fig. 7, el encuadre pasaría de unas 631 a unas 330 unidades de ancho: las piezas se verían 1,9 veces más grandes y el resorte 5 superaría los 24 px.
   - Sirve para todas las láminas. Los grupos que hoy encuadran bien no cambian.
2. **Fig. 10, «Aceite del motor»:** junta la varilla (arriba del cárter) con el perno de drenaje (abajo). Por eso el grupo abarca todo el cárter y la varilla queda chica en el celular.
   - **Opción:** dividirlo en «Varilla» y «Drenaje», que además son dos tareas distintas para el motero (medir el nivel y cambiar el aceite).
   - **Otra opción:** dejarlo y confiar en el 1 cuando se desarme.
3. **Fig. 10, lenguaje:** cambiar «Tapa 2» por un nombre de lugar, como «Tapa del respiradero».
4. **Fig. 10, menores:** el respiradero 29 está en 23 px, y los bordes de la 10 y la 30 que asoman con el grupo armado no responden.

## Estado de las ocho láminas (medible, según piloto-esquema, coincide con lo mío)
Freno 4,8 · CVT 4,72 · fig. 26 4,88 · fig. 8 4,88 · fig. 24 4,8 · fig. 11 4,88 · fig. 7 4,72 · fig. 10 4,8. Todas aprueban.
