# Qué piezas llevan modelo 3D en la ficha

**Regla:** el 3D se pone donde enseña algo que el dibujo plano no muestra. Si la pieza es común, sale sola y gratis.

## 1. Piezas comunes: siempre, sin trabajo extra
Estas piezas van en el JSON con `"comun"` (ver `piezas-comunes.js`): tornillo, tuerca, arandela, anillo de seguro, retén, O-ring, rodamiento, buje, resorte, pasador y pieza de revolución por perfil. Llevan 3D automáticamente: el motor arma su `forma3d` con las mismas medidas del dibujo. Para quitarlo, `"sin3d": true` en la pieza; por ejemplo, si son 6 tornillos iguales y basta con verlo en uno.

## 2. Piezas propias: solo si cumplen al menos una de estas condiciones
- **Su forma no se entiende de frente.** Conos, copas, cuellos o canales por detrás: poleas, campana, rampa, carrier, pistón, cáliper.
- **Lo que falla está en una cara que el dibujo no muestra.** Por ejemplo, las ranuras del cuello de la polea trasera, los canales de los rodillos o el escalón que dejan las zapatas en la campana.
- **El usuario la tiene que reconocer en la mano para comprarla o revisarla.** Correa, pastillas, zapatas, disco.

Si no cumple ninguna (tapas planas, láminas, clips, mangueras), no lleva 3D.

## 3. Cómo describirlas, de lo más barato a lo más caro
1. **De revolución:** `{"tipo":"torno","perfil":"@nombre"}`, con el perfil una sola vez en `perfiles` del JSON. Una pieza común `"revolucion"` con el mismo `@perfil` también dibuja su arte 2D. Toma 2-5 minutos.
2. **Planas con agujeros:** `prisma` con `contorno` y `huecos`, que son cortes reales: círculos, polígonos u óvalos, con `repetir`. Sirve para ventanas de la campana, agujeros de un disco, rampa de 3 brazos o placas. Toma 5 minutos.
3. **Combinación de primitivas:** `torno`, `sector`, `prisma`, `caja`, `cilindro`, `esfera`, `resorte` y `correa`. Toma 10-15 minutos.
4. **Caras o ranuras sobre superficies curvas** (ranuras helicoidales, canales en un cono): `caja` oscura como calcomanía. Hacer cortes de verdad ahí exigiría CSG y no compensa.
5. **Fundidas irregulares** (cáliper, tapas, soporte): solo si el punto 2 de arriba lo justifica, y se aproximan con 3-6 primitivas. Si toma más de 30 minutos, no se hace.

## 4. Control
El validador (`mas_controles.py`) revisa los tipos, las medidas necesarias, los perfiles `@` y que la pieza común exista. Para revisar a ojo, usar el montaje de 4 vistas por pieza (`Esquema3D.captura(v)`), con una sola captura para toda la lámina.
