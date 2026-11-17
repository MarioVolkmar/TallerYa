# Lámina 5 de 5 · Honda CB 125F (GLH125SH) · suspensión trasera (fig. F-22-1)

Página: `motor/cb125f-suspension-trasera.html` · archivo único: `motor/prueba-cb125f-suspension-trasera.html`.

**Figura elegida:** F-22-1 «Swingarm/Chain case» (columna SH). Trae la tijera, su eje y tuerca, el brazo del freno con su tornillería, la cadena, el eslabón de unión, el guardacadena y el deslizador: 14 refs. Los amortiguadores y sus bujes vienen aparte, en la F-23, y aquí salen solo de contexto.

**Hermana: ninguna.** La horquilla no comparte ni una pieza y la NKD tampoco (rueda y freno de tambor). Copié solo el estilo y las ayudas de `nkd-transmision-arte.js`. El único arte propio es la tijera; lo demás sale de la biblioteca (placa, cadena, tornillos, tuercas, arandelas, pasador).

## Tiempo (metricas.py, minutos de reloj)
| fase | real | presupuesto |
|---|---|---|
| catálogo | 2,0 | 1,5 ⚠ |
| dibujo + contenido | 7,0 | 4 ⚠ |
| verificación (validación 0 + mediciones 2) | 2,0 | 2,5 |
| revisión (correcciones) | 1,0 | 1,5 |
| espera de la revisora (aparte) | 2 | — |
| **Total con revisión** | **13** | 10 (faltaron 3) |

- **Mediciones completas: 2.** La primera, sin bloqueantes, dio 3,5 en el criterio 6 porque las marcas de «Cadena» y «Tijera» se rozaban a 360. Moví las marcas, y como eso cambió el layout, la skill pide repetirla: la segunda aprueba con 4,88.
- Previa: 1. `regresion.py`: OK (8 s; validador de 20 láminas con 0 errores).
- Ninguna fase llegó al corte (✋).

## Tokens
- **Creación:** unos 140 k (de ~70 k a 208 k). El inicio es estimado, porque la sesión venía compactada de la lámina 1.
- **Revisora:** 95,8 k.

## Notas
- **Medible:** 4,88 (6: 5 · 8: 4,7 · 9: 5 · 10: 5 · 11: 4,8 · 12: 4,8).
- **Criterio 6:** aprueba (5) tras separar las marcas.
- **A ojo** (UX 1, 2, 3, 4, 5 y 7): 4, 4, 4, 4, 5, 4; promedio **4,2**, bajo la base de 4,5. El dibujo queda chico a 1280 y el «Cómo funciona» es más simple que el de la CVT. Está explicado en `explicacion`.
- **Revisora:** mecánica **4,0** y UX **4,3**, antes de corregir. No hubo segunda revisión.

## Hallazgos (15)
- **Graves (3, todos de texto; dos son de la misma ficha 9):**
  - un «por eso» que no se seguía en «Cómo funciona» (holgura de la cadena);
  - la tuerca del eje de la tijera estaba como «autofrenante con freno de plástico», sin fuente: el catálogo dice solo «flange». Ahora dice «con brida» y la decisión es «reutiliza».
- **Menores (12):**
  - la arandela de presión es de 10 mm y no puede ir con la tuerca de 8 mm;
  - faltaba el aviso de la precarga (los dos amortiguadores igual, sin saltar de 1 a 5);
  - «precarga» y «bujes» sin explicar;
  - dónde se mide la holgura;
  - aflojar contra quitar la tuerca;
  - un eslabón de «Si falla» que no se seguía.
- **Cómo se corrigieron:**
  - 12 por script (`aplicar_hallazgos.py integrada`);
  - 2 a mano, en el script de textos: la ficha 9, con el cambio de decisión, síntomas y fallas;
  - 1 de UX es del motor y no lo toqué: el panel muestra «Seguir con: …» antes de tocar nada.
- **Falsos positivos:** ninguno de la revisora.
- **Avisos de la máquina:** el validador pide fuente para «6 mm» y «12 mm», que son medidas del propio catálogo. Lo resolví agregándolas a `fuentes.seguro`.

## Qué falló (con su sección de la skill)
1. **Paso 1, extractor Honda:** `extraer_catalogo.py --figura F22-1 --columna C --saltar 2U` leyó 9 de 14 refs. Se saltó las que tienen un código sin sufijo (`92812-20000`, `94101-08000`…) y la que tiene la descripción en dos líneas (ref. 7, tijera). Las agregué a mano al catálogo.
2. **Leer poco, `buscar_manual.py`:**
   - `buscar_manual.py honda-cb125f` responde «sin manual»: la carpeta de la CB 125F no está en `MANUALES`, así que hay que pasarle la ruta del PDF.
   - El índice no sirve: el PDF no trae títulos de sección.
   - `manual-cb125f.pdf` es el manual del propietario, no el de taller. Por eso no hay torques del eje de la tijera ni del brazo (quedaron en `pendientes`).
3. **Paso 3b, sin hermana:** la skill solo dice «biblioteca de ruedas y transmisión», pero no da ninguna lámina de suspensión trasera ni esqueleto de arte para una tijera. Lo que más tiempo tomó fue el «Cómo funciona» hecho de cero. `anexo-funciona.md`, «Suspensión», está pensado para la horquilla (barra con corte); la tijera necesita un giro sobre el pivote y la cadena.
4. **Paso 2, esqueleto:** propuso 4 grupos (guardacadena con eslabón, deslizador solo, tijera con toda la tornillería del brazo, pasador solo). Los rehice por función.
5. **Paso 9, revisión:** al cambiar las marcas de grupo por el criterio 6 hubo que repetir el `--final` (+2 min). La previa no mide el roce de las marcas a 360.

## Cambios que propongo (no aplicados)
- `extraer_catalogo.py` (Honda):
  - aceptar códigos de 5+5 sin sufijo (`\d{5}-\d{5}(-\w+)?`);
  - unir las descripciones partidas en dos líneas (ref. con `*NH303M*` y color).
- `buscar_manual.py`: agregar `honda-cb125f` a `MANUALES` y avisar si el PDF es del propietario (sin torques de chasis).
- `esqueleto_v2.py`: familia «tijera/suspensión trasera» (tijera, eje y tuerca de la tijera, deslizador, brazo del freno con su tornillería, cadena con eslabón, guardacadena con tornillos).
- `anexo-funciona.md`: esqueleto «Suspensión trasera (tijera y amortiguadores)», con la tijera que gira, el amortiguador que se acorta, la holgura de la cadena y los bujes. Puede partir de este arte.
- `--previa`: medir también el roce de las marcas de grupo a 360. Así no hace falta una segunda medición completa.
- `mas_controles.revisar_cifras`: tomar como fuente las medidas del `cat` de la propia ficha («NUT, FLANGE, 12MM»).
- **Motor (para Auxiliares):** el «Seguir con: …» del panel aparece antes de cualquier toque. La revisora lo marca como confuso.
