# Formato del JSON de la lámina (el validador lo revisa todo)

`M` = `informes_noche/piloto-esquema/motor`. Ejemplo completo: una lámina del mismo sistema (`M/datos/nmax-fig22.json` para frenos) o la CVT (`nmax-fig12.json`); de ahí basta con un par de piezas, un paso y una ficha.

## Campos obligatorios
- `lamina`, `moto`, `figura`, `arte` (clave del módulo de arte) y `refsFigura` (todos los números del catálogo).
- `cabeza{cinta,titulo,aviso}`, `visor{titulo,sub}`, `textos{pestanasAria,laminaAria,introFunciona,introCadenas,introCuando}` y `pie`. Los textos van cortos: un título o un aviso de dos líneas le quita alto al dibujo a 1280.
- `encuadreArmado [x,y,w,h]`, con proporción 900:700 exacta, y `radioToqueMin` (9 px).
- `piezas[]`: `{id, n, arte, args?, anc:[x,y], et:[dx,dy], vis:"arm"|"exp", chica?}`, o con `comun` en vez de `arte` (ver abajo).
  - `n` es el número del catálogo y `id` es único.
  - `anc` es el punto de la pieza y `et` el corrimiento del número.
  - `vis` es «arm» si la pieza se ve armada y «exp» si solo se ve desarmada.
  - **El orden es el de pintura:** lo último tapa lo anterior, también el área de toque de los números.
- **El mismo número en dos lugares** (un perno de unión en cada punta de la manguera, un par de pastillas): una pieza por lugar, con `id` distinto y el mismo `n`: `{"id":"16a","n":"16",…}` y `{"id":"16b","n":"16",…}`.
  - Basta un número visible en el armado (`vis:"arm"` en uno, `"exp"` en el otro).
  - Cada `id` sale en su propio paso; `sujeta` y `pasos[].m` usan el `id`, no el `n`.
  - Varias piezas iguales que salen juntas van como una sola, con `p.copias`.
- `contexto[]` (opcional): piezas de otras láminas, con `{arte, despuesDe:"<id>" | alPrincipio:true | alFinal:true, alFrente, clase}`.
  - **`alPrincipio`**: se pinta antes de todas las piezas. Úsalo para manubrio, chasis o carcasas de fondo, así no tapan ningún número ni su área de toque.
  - `despuesDe` deja el contexto encima de las piezas anteriores, y puede tapar sus números en el despiece (medir_lamina lo marca como «→rect»).
  - Si el contexto tiene ficha, el arte lleva `data-ctx="<clave>"` y la ficha `ctx:true`.
- `pasos[]`: `{m:{id:[dx,dy]}, t:"texto"}`. Los corrimientos se suman paso a paso. `textoArmado` es el texto del estado armado.
- `nombres{n:"nombre corto"}` (para lectores de pantalla), `ocultas[]` (números que la carcasa tapa en el armado) y `ordenChips[]`.
- `fichas{n:{nombre,cat,que,sirve,fallas[[causa,texto]],sintomas[],cuando,decision:"repara"|"cambia",compra,dif:"facil"|"media"|"taller",conecta[],efectos[[n,texto]],certeza[["ok"|"ap",texto]]}}`. En v2 cambian algunos campos: ver «Modelo v2».
  - Las causas posibles son desgaste, calor, humedad, maluso, golpe y edad.
  - Una ficha con `ctx:true` es de una pieza de otra lámina.
- `cadenas[]`: `{t, p:[[n,texto]...]}`, con eslabones de piezas distintas.
- `cuando[]`: `{que, cuando, fuente, tarea?}`.
- `funciona{vbCelular, vbEscritorio, pasos:[{t, s:{…estado…}}]}`.
- `fuentes{seguro[], aproximado[], lista[]}`, en HTML corto.
- **Clases:** solo con `esq-`, también dentro del SVG de «Cómo funciona», y nunca `esq-ficha`, `esq-titulo` ni otra que ya exista en `tallerya.css`.

## Campos que se agregaron después
- `"catalogo":"nmax-bbe4"`: archivo de `M/catalogo/`. Los números de la figura salen de ahí; `refsFigura` queda solo como respaldo.
- `"intervalos":"yamaha_nmax_155"`: archivo de `garaje/intervalos/`.
- `"comun":{"atras":[0.5,-0.32],"sombra":"url(#xxSombra)","colores":{"acero":"url(#…)","cromo":…,"rosca":…,"plast":…,"estrias":…}}`
  - `atras` es hacia dónde va el espesor en pantalla, por unidad de profundidad.
  - Los colores son los ids de las `defs` de tu arte; los que falten toman un gris por defecto.
  - Se pueden agregar colores propios (p. ej. `"cobre"`) y usarlos con `p.material`.
- `"sujeta":{"<id que sujeta>":["<id sujetado>",…]}`: el validador comprueba que lo que sujeta salga antes que lo sujetado o en el mismo paso.
- `"carcasas":[{"id","transparente":0..1,"rayosx":0..1}]`: activa el botón «Transparente». Suma una fila de controles a 360 (proximidad 4,7 en lugar de 4,8): ponlo solo si hay piezas internas que no se ven de otra forma.
- `"perfiles":{"polea13":[[r,z],…]}`: perfil de revolución cerrado, con z hacia el lector. Se usa con `"@polea13"`.
- `cuando[i].tarea`: clave de la tarea en intervalos, donde se comparan km y años. Si la fila no coincide con los km y días de esa tarea, va sin `tarea`. `cuando[i].fuente` termina con `<span class="esq-s-ok">Seguro</span>` o con `esq-s-ap`.
- `fichas[n].cat`: «DESCRIPCIÓN DEL CATÁLOGO · 1 pieza», «· 1 juego (2 pastillas)» o «· 3 piezas», con la cantidad del catálogo.

## Módulo de arte (`<lamina>-arte.js`)
Define `ESQ_ARTE["<lamina>"]` y exporta `return {defs:DEFS, <funciones arte*>, funciona:{svg, aplicar}}`. El validador lee los nombres entre `defs:DEFS,` y `funciona:`.
- `defs`: degradados y filtros con ids propios de la lámina (prefijo, p. ej. `b26`).
- Espesor («extruir»): copias del contorno corridas hacia `atras`; borde solo en la del fondo, las intermedias sin borde (ejemplo: `extruir` en `M/datos/nmax-fig1-arte.js`).
- `montar()` (opcional): corre después de escribir las defs.
- Las funciones `arte*` que nombran `piezas` y `contexto` devuelven SVG. Para dibujar la misma pieza en espejo (izquierda y derecha), pasa el lado en `args`.
- **Piezas internas** (kit de la bomba, diafragma, pistón): pon `class="esq-oculto-arm"` en su `<g>`. No se ven en el armado, aparecen al moverlas en el despiece y se ven en «Transparente». Así no importa que vayan antes o después de la carcasa.
- `funciona:{svg, aplicar(s,$)}`: el SVG del esquema y cómo cada estado `s` mueve sus partes. `$` es `getElementById`. Para grupos de elementos usa una clase `esq-…` y `document.querySelectorAll("#fn .esq-…")`.

### «Cómo funciona» en el celular (≤ 700 px)
- El `<svg id="fn">` cambia de `vbEscritorio` a `vbCelular`.
- **`<g id="fnCorte">`** se corre `translate(-470px, 262px)` con el CSS del motor. Lo que está a la derecha de x = 470 en el escritorio queda debajo en el celular. Diseña el esquema principal en x 0-470 y y 0-300; lo secundario (cáliper, rueda) va a la derecha, dentro de `#fnCorte`, con y ≥ 40.
- `class="esq-solo-pc"` y `class="esq-solo-movil"` muestran un elemento solo en un tamaño. Úsalas, por ejemplo, para una manguera que en el escritorio va a la derecha y en el celular baja.
- En el celular los textos `.esq-fn-et` suben a 19 px. Con `data-xm` y `data-ym` en un `<text>` se le da otra posición x/y en el celular.
- Las transiciones de tus ids van en línea (`style="transition:transform .7s"`): las del CSS del motor son solo para los ids del freno. Para un giro: `style="transform-origin:Xpx Ypx"`.

## Piezas comunes: `{"id","n","comun":tipo,"p":{…},"anc","et","vis","marco"?,"sin3d"?}`
Todas se dibujan **de frente, con el eje hacia el lector** (el vástago o el espesor van hacia `comun.atras`): decide la vista de la lámina según eso. `p.x` y `p.y` son el centro de la cara de adelante. `"oculto":true` (en la pieza, fuera de `p`) la esconde armada, como `esq-oculto-arm`. Las medidas van en unidades del dibujo. Opcionales en todas: `p.copias:[[dx,dy],…]` (varias iguales) y `p.sombra`.

| tipo | p (obligatorio en **negrita**) |
|---|---|
| tornillo | cabeza (radio, 10), brida (radio, 0 = sin brida), largo (46), d (12), tipo:"allen", alto |
| tuerca | r (14), alto (8) |
| arandela | **r, ri**, e (3), material:"plast" o un color propio de `comun.colores`, lado (color del canto) |
| seguro | **r** |
| reten | r (20), ri, ancho (5) |
| oring | **r**, g (grosor, 3) |
| rodamiento | **r, ri**, ancho (8), tipo:"agujas" (n), bolas:false, pista |
| buje | **r, ri, largo**, estrias:true, material |
| resorte | **r, largo**, vueltas (6), alambre (3.2) |
| pasador | **r, largo**; cuerpo:"lateral" (vástago de lado, solo desarmado) + **cabeza** |
| revolucion | **perfil** ([[r,z],…] o "@nombre"), cara, lado: arte 2D y 3D desde el mismo perfil |
| manguera | **puntos** ([[x,y],…] relativos a x,y; curva suave), g (grosor, 9), color, boca (color de los casquillos), extremos:false |
| abrazadera | **r**, tipo:"tornillo" (sin fin) o de orejas (por omisión), giro (grados hacia donde salen las orejas, −90 = arriba), banda (5), ancho (2,2), oreja |
| caja | w (80), h (60), rx (8), prof (14), tapa (true o el margen), caraTapa, cara, lado, tornillos [[dx,dy],…], bocas [[dx,dy,r],…] |
| ducto | **puntos**, r0 (14), r1 (boca, = r0), cara, lado, boca:false: tubo que se ensancha, con la boca hacia el lector |
| placa | contorno [[dx,dy],…] (rect 60×40), huecos [[dx,dy,r],…], e (2), material:"fibra" (empaque), "acero", "caucho" o un color de `comun.colores` |

Las formas de lámina (manguera, abrazadera, caja, ducto, placa) sirven para admisión, escape, refrigeración y carrocería. Su 3D es una maqueta simple (tubo recto, caja redondeada, placa con huecos); solo con `con3d`.

El vástago del tornillo es un `rect` que solo se ve en el despiece, y puede tapar el número de una pieza pintada antes.
`marco`: nombre de un transform que exporta el arte en `marcos:{…}` (p. ej. `LOC` del cáliper del freno), para dibujar la pieza en ese plano.

## forma3d (piezas propias): `fichas[n].forma3d = {"partes":[…]}`
Cada parte es un objeto plano con `tipo`: `{"tipo":"torno","perfil":"@x","color":"acero"}`, `{"tipo":"cilindro","r":9,"z":[0,6],"pos":[32,0],"repetir":6}`, `{"tipo":"caja","tam":[x,y,z],"pos":[x,y,z]}`; abajo, los campos de cada tipo.
El eje de la pieza es z. Cada parte acepta `color` (alum, acero, aceroOsc, oscuro, caucho, friccion, plast, rodillo, campana, campanaClara o #hex), `giro` (grados) y `repetir` (n copias en círculo).
- `torno` {perfil}
- `sector` {r:[ri,ro], ang:[a0,a1], z:[z0,z1]}
- `cilindro` {r, z, pos, esc}
- `caja` {tam, pos, rot}
- `prisma` {contorno:{n,r,giro} o [[x,y]…], z, pos, huecos:[{r} · {n,r,giro} · {r:1,ovalo:[rx,ry],pos,repetir,giro0}]} → **cortes reales**
- `esfera` {r, pos, z}
- `resorte` {r, largo, vueltas, alambre}: va de z = 0 a z = −largo, sin `pos`
- `correa` {c1, r1, c2, r2, seccion:{arriba,abajo,alto}, dientes:{paso,hondo}}

Ejemplo de cortes reales: la placa del fondo de la campana, en `M/datos/nmax-fig12.json`, ficha 24. Ejemplo de kit (pistón con copas y resorte): `M/datos/nmax-fig26.json`, ficha 2.

## Modelo v2 (el de siempre desde nov-2026: toda lámina nueva lleva `"v2"`)
El motor es uno solo (`esquema.js` + `esquema.css`); un JSON sin `v2` se ve con el modelo viejo (respaldos `…-v1.json`).
Ejemplos: frenos → `M/datos/nmax-fig26.json` (con lados) o `nmax-fig22.json`; otros sistemas → `nmax-fig12.json` (sin lados).
- `v2 = {grupos[], con3d[], toqueExtra[], inicio?, lados?, ladoTxt?, ladoAria?, lado?, conjunto3d?, deriva?}`
  - `grupos[i] = {id, nombre, corto?, lado?, piezas[ids del dibujo], torn[{nombre, corto, ids[], cant, marca?}], pasos[índices de D.pasos], marca?[x,y]}`.
    - Cada id de `piezas` va en un solo grupo, y todos los ids tienen grupo (si no, no se pueden tocar). `9a` y `9b` se listan como ids; la lista y la ficha los muestran como la ficha 9.
    - `torn`: tornillería agrupada por punto de unión; su píldora se pone sobre la primera pieza.
    - `pasos`: los pasos de `D.pasos` que mueven el grupo, en orden; «Desarmar» suma solo lo de las piezas del grupo. Un paso puede estar en dos grupos.
    - `marca`: dónde va la píldora del grupo (por omisión, el centro de sus piezas). Ponla a mano si dos grupos quedan encimados (p. ej. el clutch dentro de la campana).
  - `lados` solo para conjuntos repetidos (`{"del":"Delantera","tra":"Trasera"}`, con `ladoTxt` `{"del":"freno delantero",…}` y `ladoAria:"Freno"`). Sin `lados` no hay selector.
  - `con3d`: fichas con visor 3D (solo formas difíciles de imaginar); las piezas comunes ya no traen 3D si no están aquí.
  - **Toque mínimo automático** (desde nov-2026): en la vista de grupo, toda pieza (o racimo de partes sueltas, como rodillos o clips) de menos de 24 px recibe un círculo invisible de 24-30 px, recortado a la mitad de la distancia a la vecina. Casi nunca hace falta `toqueExtra`.
  - `toqueExtra`: ids de piezas muy chicas y compactas (una sola, no con copias alrededor de un eje: el círculo va al centro de su caja y taparía todo lo de adentro) que llevan un círculo de toque invisible. Pocas: tapa a las vecinas; si una vecina deja de recibir el toque, píntala después (orden de `piezas`).
  - `inicio`: título de la ficha vacía («Piezas de la CVT»).
- **Fichas v2:** `que`, `sirve`, `sintomas[]`, `fallas[[causa,texto]]`, `decision` (repara | reutiliza | cambia), `porque`, `dif` (facil | taller), `cuando`, `arrastra[]` («causa → efecto en [[n|pieza]]»), `conecta[]`, `cat`, `codigo` (del catálogo), `certeza[]` (la lista que abre «Fuentes») y `certezaDe`.
  - `certezaDe = {que, sirve, sintomas, fallas, porque, cuando: "ok"|"ap"}`: pone la marca chica «✓ manual» o «≈ aprox.» al final de cada dato. «ok» solo si sale del catálogo o del manual.
  - Ya no van `efectos` ni `compra` (los reemplazan `arrastra` y `porque`).
- En el celular la ficha sale en una hoja inferior (asoma con el nombre y «Qué es»; se sube para verla entera); en el computador, al lado del dibujo.

## Estilo v2 (prosa de todas las láminas)
- Prosa en segunda persona, frases cortas, acciones concretas («Revísala si…», «Cámbiala cuando…»).
- Sin «(N)» ni nombres de catálogo en la prosa: la pieza se nombra con un enlace `[[n|texto]]`; el nombre de catálogo y el código van solo en «Para pedirla» (salen de `cat` y `codigo`).
- **Se acorta la explicación, NUNCA la seguridad.** No se quitan:
  - los avisos de seguridad (vaciar con jeringa antes de soltar una unión, tapar la pintura, manubrio recto);
  - los pasos de cierre (piezas nuevas, líquido nuevo, purgar —con ABS, en el taller— y probar los frenos con la moto quieta antes de rodar);
  - las marcas de apriete o de posición (la marca de la abrazadera, el orden de apriete y el torque del manual de servicio).
- Los pasos de un conjunto repetido dicen de qué lado son en el título («Bomba trasera (izquierda) · …»).
- `decision` puede ser `repara`, `reutiliza` (p. ej. un perno hueco sano) o `cambia`; tiene que decir lo mismo que `porque`.
- Si la v2 sale de una v1, `v2.deriva` nombra el JSON de origen: el validador avisa si en la v2 falta una frase de seguridad o de cierre que estaba en la v1.
