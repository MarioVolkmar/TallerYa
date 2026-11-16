# Brief: hacer una lámina del esquema desde cero (una página)

**Meta:** una lámina de la NMAX (u otra moto) con el nivel del freno de la v8: dibujo propio armado y desarmado, números que se tocan bien, una ficha por pieza, «Cómo funciona», «Si falla» y «Cuándo».

**Se toca solo:** `datos/<lamina>.json` y `datos/<lamina>-arte.js`, más una página (copia de `freno.html` con las dos rutas cambiadas).
- El motor (`esquema.js`, `esquema.css`) no se toca. Si le falta algo, se avisa a Auxiliares.
- `garaje/diagramas.py` es de la sesión de dibujos: solo se lee.

## 1. Qué leer (en este orden, por rangos)
1. `datos/nmax-fig22.json`: el ejemplo completo. Basta con un par de piezas, un paso y una ficha.
2. `datos/nmax-fig22-arte.js`: cómo se dibuja una pieza (funciones que devuelven SVG) y qué exporta el módulo.
3. `../criterios-ux.md` (la rúbrica) y la sección v8 de `../cambios.md` (lo aprendido de toques y encuadre).
4. Para el contenido:
   - `garaje/despiece_mapas/<moto>.json` (figura, título y palabras clave);
   - `despiece_local/marcas_*.py` (números de la figura, solo local);
   - borradores de ficha en `garaje/despiece_fichas.py`, `despiece_guia_mecanica.py` y `despiece_glosario.py`;
   - intervalos en `garaje/intervalos/<moto>.json`.
5. Las fotos y planos del fabricante solo se usan como referencia de forma: nunca se copian ni se publican.

## 2. Formato del JSON y del módulo de arte
Está en `.claude/skills/hacer-lamina/anexo-formato.md` (campos obligatorios y lo agregado después). Para una lámina nueva, usar la skill `hacer-lamina`.

## 3. Validar sin navegador (segundos)
```
python validar_esquema.py datos/<lamina>.json        # o con --refs 1-33 si no hay refsFigura
```
- Revisa campos, números de la figura con pieza y ficha, referencias de pasos, chips y cadenas, arte exportado, encuadres, toques y clases.
- No ve si el arte de una pieza tapa el número de otra: eso se mide en el navegador.

## 4. Medir en el navegador
1. `python armar_un_archivo.py datos/<lamina>.json` y abrir `prueba-<lamina>.html` en el panel.
   - Hay que volver a navegar con `?v=N`.
   - `resize_window` va justo después de navegar.
   - Con el panel oculto se congelan las animaciones: usar `window.__esq` (`aplicar`, `ponerVista`, `fijarVB`).
2. **Toques:** `elementFromPoint` en el centro de cada número visible (armado y despiece, Normal y Transparente) a 360, 390 y 1280.
   - Todos tienen que caer en su propio número.
   - A ±9 px del centro en 4 direcciones, **0 roces**.
   - `integracion/medir_toques.js` sirve con los selectores en `esq-` (`.esq-pz`, `.esq-et`, `.esq-bola`).
3. **Distribución:** `integracion/medir_distribucion.js` (con `.esq-escenario` y `.esq-envoltura`) a 360×740, 390×844, 1024×768 y 1280×800, más botones de 44 px y sin desborde.
4. Una sola captura final (`scale: 0.5`) como prueba visual.

## 5. Terminado quiere decir
- [ ] `validar_esquema.py` da **OK**, sin errores.
- [ ] Toques: el 100 % de los números en su centro y 0 roces a ±9 px, a 360, 390 y 1280.
- [ ] Rúbrica `criterios-ux.md`: ningún criterio por debajo de 4 y ningún bloqueante. El dibujo mide al menos 235 px de alto a 360.
- [ ] Cada número del catálogo tiene pieza dibujada (o va en la tornillería agrupada, con un número tocable) y ficha completa.
- [ ] Cada dato dice si es seguro o aproximado, con su fuente en `fuentes` y en la `certeza` de cada ficha.
- [ ] Sin errores en la consola y la página funciona sin red, salvo las fuentes de Google.
- [ ] Nota en `../cambios.md` y relevo en `informes_noche/relevos/`. Sin commit hasta que el usuario lo pida.
