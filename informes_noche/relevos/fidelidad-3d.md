# Relevo: fidelidad de los modelos 3D (sesión "Fidelidad 3D")

## Estado (sin commit)
- Las 25 líneas rediseñadas por familia y por línea; cargan sin errores. Lotes 1, 2 y 3 enviados al Auditor 3D; falta que mida los lotes 2 y 3.
- Alta: 36,5k–56,9k triángulos, 44–53 calls (sin sombras; el Auditor mide unas 5 más con sombras) y 15 programas. Baja: ≤34,4k medido antes del lote 3.
- Luces: faro con reflector, fuente y mica; stop y 4 direccionales con reflector. Las lentes se sacan solas a la superficie (`vestirLuces`).
  `construirMoto` devuelve `anclas` = { faro, stop, direccional_di, direccional_dd, direccional_ti, direccional_td }, que Modelos 3d ya usa.
- Lo translúcido del modo Moto venía de `moto3d.js` y ya lo corrigió Modelos 3d.

## Pendientes concretos
Hecho el 14-11: baja medida tras el lote 3 (RC era 35,3k → 34,9k con `panelAhusado(..., tosco)` en quilla y carenado negro; las demás ≤34,5k).
Alta: 36,5k–55,8k tri, 38–49 calls sin sombras. Perfiles XTZ, NKD, Aerox y Apache revisados: bien.
Luces: prueba de rayos en las 25 (`media/_ocl3d.js`, `__oclTodas()`: faro, stop y 4 direccionales desde 3 ángulos). Arreglado:
`vestirLuces` ahora cuenta `M.pintura2` y saca lentes hundidas hasta 9 cm (stop de Dynamic y Aerox), y el stop de la familia semi va
en la punta de la cola (Best y Crypton). Única "falla" restante: faro de la Aerox, falso positivo (el ancla cae en el hueco entre los dos faros).
1. Falta el visto bueno del Auditor 3D (no aparece entre las sesiones abiertas): frente de RS/RC menos "huevo", faros de Duke/MT en 3/4, y medir con sombras.
2. Riesgo de calls: con sombras deberían quedar ≤54 (NMAX 49 la más alta).

## Archivos clave
- `garaje/static/garaje/js/moto3d/rasgos.js`: solo datos. FAMILIAS (naked, clasica, carenada, scooter, semi, enduro) y LINEAS (regex → rasgos).
  Una línea puede declarar `familia`; así la CR4 y la NKD van como naked.
- `garaje/static/garaje/js/moto3d/construir.js`:
  - carrocerías: `carroceriaCalle`, `aletasNaked`, `carroceriaSemi`, `carroceriaScooter`, `carenadoDeportivo`, `carroceriaNmax(aerox)` (Aerox incluida) y `carroceriaEnduro`;
  - faros por `R.faro.forma`; escape por `R.escape.forma` (bajo, corto, clasico);
  - helpers `sobre`/`pegar` (rayo contra la superficie), `techoSobre` (cuelga soportes del colín), `vestirLuces`, `anclasLuces`, `unirLados` e `instancias` (siempre una malla normal, sin InstancedMesh).
- `comun.js` (subdividir 0,15 en baja), `cache.js` (CACHE_VERSION 5; súbela si cambian paneles cacheados), `geometria.js` (une mallas desde 2 por material).
- No toques `moto3d.js`: es de Modelos 3d.
## Cómo probar
- Arnés local `media/_arnes3d.js` (no va al repo). Ábrelo en http://localhost:8001/garaje/1/vista-3d/ y ejecuta:
  `eval(await (await fetch("/media/_arnes3d.js",{cache:"no-store"})).text())`.
- Uso: `await __probar("duke")` mide tri y calls; `__todas()` + `__res` mide las 25 en segundo plano; `await __lote([...])` y `await __hoja([...],2)` arman la hoja de perfiles.
- `__L` guarda las fichas; regenéralas desde LineaMoto cuando el Auditor mecánico cambie una.
- Recarga la página entre cambios de código: los módulos quedan en caché.
- El servidor de :8001 es de otra sesión y se cae a ratos: espera y reintenta.
- Para medir como el Auditor: espera unos 6 s tras cargar y llama `__visor.cuadro()` y luego `info()`. Para la noche: `__visor.vivo(true, true)`.

## Reglas
- Todo en español. Sin commit hasta que el usuario lo pida.
- Reporta a Auxiliares (local_9657d3fe-d634-45af-9c61-9d6539d08def) solo al TERMINAR una tarea completa, en 3–5 líneas; nunca "recibido" ni "sigo".
- Lo técnico se coordina directo con el Auditor 3D (local_0527f3f5-c61f-4148-a735-459b6ff12066).
- Una sola medición o prueba pesada a la vez en todo el proyecto. Capturas solo si hacen falta (hoja de perfiles, no una por moto).
- Rasgos con anclas y por familia o línea, nunca números sueltos para una sola moto. Presupuesto: ≤60k triángulos en alta, ≤35k en baja, ≤60 calls y ≤16 programas.
- Las luces usan M.luz, M.stop y M.ambar (0xffb347); no crees materiales nuevos para luces.

## 14-11 (2.ª ronda, pedidos del Auditor 3D)
- Baja: `perfil` usa menos segmentos en piezas de <10 cm y bisel de 2 pasos en baja. RC 34,9k → 32,8k (máx. de las 25); NS 32,3k; MT-03 32,3k; Duke 31,9k.
  Medir con `__med`/`__todas2` (espera 6 s; `__probar` solo da cifras corridas una moto si se lee enseguida).
- Flotantes: (a) depósito de frenos ahora sobre la abrazadera de la manigueta; (b) platina del parrillero sube con `techoSobre(..., [M.chasis])`.
  Pruebas locales: `media/_flot3d.js` (cajas sueltas) y `media/_ocl3d.js` (luces tapadas).
- CR4: misma geometría, calls, materiales, programas y armado que la NKD; su primer cuadro varía igual que el de NKD/CB. Probablemente se midió de primera (en frío).
- El cono de día es de moto3d.js: se le pasó a Modelos 3d.
- Llantas (pedido del usuario): `despejarLlantas` empuja los vértices de cualquier `panelAhusado` que caigan dentro de una llanta a 1,2 cm de la banda.
  Más: cilindro y bujía de semi más cortos, codo y salida del escape topados detrás de la llanta delantera, depósito del amortiguador hacia afuera,
  mono de scooter a z 0,115. CACHE_VERSION 6. Prueba: `media/_llantas3d.js` → `__llantas(k, "todos", true)` / `__llantasLinea(k)`;
  estricta con `__banda=0.5; __rmin=0.62; __rmax=1`. Resultado: 25/25 sin choques (normal y estricta, con y sin accesorios).

## 14-11 (luces por modelo)
- Rasgos nuevos en rasgos.js: `faro.orejas`, `faro.visera` (redondo), `relojes` ("uno"/"dos"), `direccionales.tipo` ("redondas"/"led", `cromo`),
  `stop` ("guardabarros"/"redondo"/"led"), `rines` ("radios"/"aleacion"). Naked con `faro.forma: "redondo"` no lleva máscara (`faroRedondo`).
- Cambiaron: NKD, GN, Boxer, Eco Deluxe, Duke, MT-03. Sin fotos guardadas en el proyecto: lo demás quedó como estaba (dudosos: CR4, Dynamic, Eco Deluxe).
- `__vistas([[clave,x,y,z],...])` en el arnés arma una hoja de vistas.
- Anclas de luces (14-11): `anclasLuces` da el centro de la CARA de cada lente + `dir`; `anclas.lamparas` = una entrada por lente
  {tipo, lado, pos, dir, ancho, alto, principal}. Faro doble tapado → ancla única = lente principal. Prueba: `__anclasLente()` /
  `__anclasTodas()` en media/_ocl3d.js (25/25 ok). Stop de las semi en la punta de la cola, girado 0,4.

## Fotos de referencia (15-11)
- 24 de 25 carpetas con fotos en `manual_despiece/<moto>/fotos/` (fuentes.txt + _hoja.jpg). Falta TT 125 DS (no está en la web de AKT ni en Commons). Dudosas: Boxer, Discover, Wave, Best (pocas fotos); XTZ son de la 150.
- Cambios por foto: Aerox direccionales delanteras visibles de frente; Dynamic Pro doble faro; Dio faro en V en el escudo (`scooter.faroEscudo`); Eco Deluxe y GN rines de aleación; Eco direccionales redondas; MT-03 direccionales redondas; Discover rines de aleación.
- Presupuesto tras los cambios: alta máx. 50,5k (MT-03), baja máx. 28,8k, calls ≤44; luces visibles en las 7 cambiadas.

## Después de la 1 a. m. (15-11)
**Hecho**
- GN 125: los 2 relojes redondos flotaban (el Auditor 3D lo vio). Se añadió en `construir.js` un tubo de soporte desde la tija superior hasta cada reloj (también aplica a NKD y Boxer).
- Chequeo de piezas flotantes (`__flotTodas`, `media/_flot3d.js`): 25/25 ok. Es por cajas, más laxo que el del Auditor.
- Modelos 3d avisado: carpetas de fotos listas para las calcas de fábrica.
- Auxiliares recibió la tabla final por moto y el reporte de la GN.
- Suite completa: 189 pruebas OK.

**Pendiente**
- Que el Auditor 3D vuelva a medir la GN con su método.
- TT 125 DS sin fotos.
- Relojes y direccionales sin confirmar en varias motos (las fotos de estudio no los muestran).
- Sin commit.

**Archivos clave**
- `garaje/static/garaje/js/moto3d/construir.js`: soporte de relojes redondos, luces del escudo (Dio/Dynamic), ámbar del Aerox.
- `garaje/static/garaje/js/moto3d/rasgos.js`: Dio `faroEscudo`, rines de GN/Eco/Discover, direccionales de Eco/MT-03.
- Arneses locales en `media/`: `_arnes3d.js`, `_ocl3d.js`, `_flot3d.js`, `_dir3d.js`, `_llantas3d.js`.
