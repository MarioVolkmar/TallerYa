# Anexo: despiece completo de una línea (paso 4)

Meta: **45 min** si el formato del catálogo ya lo lee el importador; un formato nuevo es **sesión aparte**. `P` = `venv/Scripts/python.exe`.
Qué queda al final: un `Despiece` (versión) con sus `Lamina` y `ParteDespiece` en la base **local**, cada parte con nombre en español, explicación y, si aplica, la tarea del plan; el mapa en `garaje/despiece_mapas/<marca>_<modelo>_<version>.json` (sí va al repo) y las imágenes en `media/despiece/` (**solo local**).

## 1. Ubicar el catálogo (5 min)
| marca | dónde (público y legal) | formato |
|---|---|---|
| Yamaha | motoblu.co (concesionario de Medellín), catálogo por versión (`BBE4`, `B6U1`…); a veces bilingüe | `yamaha` |
| Bajaj, KTM, TVS, Victory (Auteco) | PDF de Auteco «Catálogo de partes <modelo>»; cambian de nombre con cada edición: buscar el más nuevo | `auteco` |
| Honda | Honda Latinoamérica vía accesoparts.com.bo (`MP-<modelo>…esp`) | `honda` |
| Hero | catálogo HCML (PDF) | `hero` / `hero2` (Hunk 125R) |
| AKT | aktmotos.com/catalogo-de-partes/ (abrir en el navegador; bloquea robots) | `akt` |
| Suzuki | no publica; pedir a Suzuki Motor de Colombia; catálogos viejos en PDF | `suzuki` |
| sin PDF | diagramas de una tienda en línea, con OK del usuario | `fichas` (carpeta con `fichas.json`) |
- Descargar pide el OK del usuario; se guarda en `manual_despiece/<moto>/` o `despiece_local/`. Copias de studocu: el importador borra su marca de agua al dibujar (en memoria; el PDF no se toca).
- Elige la **versión que se vende en Colombia** (tambor o disco, carburador o inyección); si hay dos vigentes, dos mapas con `variante` y `especificaciones`.

## 2. Reconocer el formato (3 min)
Mira el texto de 2-3 páginas de tabla (nunca el PDF entero):
```
P -c "import pymupdf,sys;d=pymupdf.open(sys.argv[1]);[print(i,' '.join(w[4] for w in d[i].get_text('words')[:14])) for i in range(int(sys.argv[2]),int(sys.argv[3]))]" <pdf> 10 14
```
- `FIG. 12 … REF.` → yamaha · `FIGURA Nº 12: …` → auteco · bloques `E-2` / `F-11` con letras raras → honda · `E-2 : TÍTULO` → hero2 · `E- 4` → akt · `FIG.103A (1-B-2)` o `Fig. 1 /` → suzuki. Detalle de cada lector: docstring de `garaje/despiece_lectores.py` y de `importar_despiece.py`.
- Las claves de figura cambian por formato: Honda guarda E-n como 100+n y F-n como 200+n; Hero suma 50 por letra («E-8A» = 158); Auteco admite letra («12A»).
- **No lee la tabla** (texto rotado, imagen escaneada, columnas nuevas): para; un lector nuevo es sesión aparte (cambia código compartido y necesita pruebas). Anótalo y sigue con el paso 5 o 7.

## 3. Escribir el mapa (15 min)
Parte del mapa de una moto **de la misma marca** (`garaje/despiece_mapas/`) y cambia figuras y títulos. Forma:
```json
{"marca": "Yamaha", "linea": "NMAX 155", "version": "BBE4", "anio": 2024, "formato": "yamaha",
 "fuente": "https://…", "variante": "", "especificaciones": {},
 "laminas": [
   {"figura": 22, "titulo_es": "Freno delantero", "pieza": "freno_del", "diagrama": "freno_disco",
    "reglas": {"BRAKE PAD": "pastillas-del"}, "descripciones": {"<código>": "texto corregido"}}]}
```
- `marca` y `linea` **idénticos** a la línea del paso 1 (el importador la busca por esos nombres).
- **Qué figuras:** todas las que tienen algo del plan o del diagnóstico (motor por partes, admisión/filtro, carburador o inyección, escape, clutch, transmisión o CVT, kit de arrastre o transmisión final, frenos, ruedas y llantas, horquilla, amortiguadores, eléctrico, batería, radiador). Carrocería y calcas, no. Típico: 15-24 láminas.
- `pieza` (sistema del 3D y del plan): `aceite motor filtro_aire bujia cadena correa freno_del freno_tras llanta_del llanta_tras suspension_del suspension_tras bateria refrigeracion`.
- `diagrama` (dibujo propio de TallerYa; **es lo que se publica**, el plano no): una clave de `DIAGRAMAS` en `garaje/diagramas.py` (solo leer; es de la sesión de dibujos): `freno_disco bomba_freno freno_completo freno_trasero bombas_abs freno_tambor cvt caja_secundaria transmision clutch carcasa aceite admision culata valvulas cilindro_piston distribucion carburador inyeccion escape radiador encendido electrico rueda rueda_trasera rueda_tambor suspension_delantera amortiguadores`. Si ninguno sirve, el más cercano y avisa a la sesión de dibujos en el informe.
- `descripciones` (opcional): corrige el texto del catálogo por código (ligaduras rotas, «AmorƟguador»).

## 4. Enlace pieza ↔ tarea (dentro del mapa; 5 min)
Las `reglas` de cada lámina dicen qué fila lleva qué tarea del plan (`TareaMantenimiento.clave`: `aceite cadena-lubricar kit-arrastre correa-cvt aceite-caja filtro-aire bujia valvulas pastillas-del pastillas-tras bandas-del bandas-tras liquido-frenos llanta-del llanta-tras suspension-del suspension-tras refrigerante bateria`).
- Un patrón enlaza si la descripción **empieza** por él, o si lo contiene y su primera palabra no es herraje (`HERRAJES_INICIO`): así «TORNILLO TAPA FILTRO» no se lleva el filtro. Es la **regla de la primera palabra** (skill `mecanico`).
- `"PATRÓN": null` = exclusión explícita (gana la primera coincidencia).
- Después el importador aplica solo: `REGLAS_GLOBALES` (bujía, batería, llantas, filtro de aire, líquido de frenos… en cualquier moto), `REPRESENTATIVAS` (si el catálogo no vende la pieza que se cambia: la bomba del freno para el líquido, la carcasa para el aceite de caja) y **`tarea_al_sello`**: la tarea pasa del tapón o de la tapa del filtro **a su empaque u o-ring**, y el filtro la comparte con su o-ring. No lo repitas en las reglas.
- Revisa el resultado con criterio mecánico: si una tarea cae en una pieza que no se cambia, corrige la regla (no la base).

## 5. Importar (2 min de máquina)
```
P manage.py importar_despiece <pdf o carpeta> garaje/despiece_mapas/<mapa>.json              # primera vez
P manage.py importar_despiece <pdf> garaje/despiece_mapas/<mapa>.json --reenlazar             # tras cambiar el mapa: recalcula título, pieza, diagrama, tarea, nombre y ayuda sin borrar marcas
P manage.py importar_despiece <pdf> garaje/despiece_mapas/<mapa>.json --reemplazar            # rehace las láminas: se pierden las marcas x,y
```
- Requiere PyMuPDF (`requirements-dev.txt`). «FIG. N no está en el PDF» = clave mal escrita o figura con letra.

## 6. Traducción y explicaciones (5 min)
- El nombre en español sale, en orden, de: `traducir()` de `garaje/despiece_glosario.py` (glosario curado) → el español del catálogo bilingüe → `garaje/despiece_traductor.py` (por palabras). La explicación, de `ayuda_para()` y de las guías de `garaje/despiece_fichas.py`.
- Catálogos ya en español (Auteco, AKT, Hero, Yamaha Colombia) dejan `nombre_es` vacío y muestran la descripción: está bien.
- Revisa: `auditar.py <palabra>` (columna Trad.). Por debajo de 95 %: lista las descripciones en inglés sin traducir y súmalas al glosario (un renglón por pieza, **regla de la primera palabra**, nombre corto en el español de Colombia de la skill `mecanico`); luego `P manage.py traducir_despiece` (recalcula nombres y explicaciones de todas las motos sin tocar marcas).
```
P -c "import os,sys,django;sys.path.insert(0,'.');os.environ['DJANGO_SETTINGS_MODULE']='config.settings';django.setup();from garaje.models import ParteDespiece as P;[print(d) for d in sorted(set(P.objects.filter(lamina__despiece__linea__nombre=sys.argv[1],nombre_es='').values_list('descripcion',flat=True)))[:40]]" "<nombre de la línea>"
```

## 7. Verificar (5 min)
```
P manage.py auditar_tareas_despiece            # cada tarea del plan tiene pieza y el visor abre en ella
P .claude/skills/agregar-moto/auditar.py <palabra>
P manage.py precalentar_despiece               # deja el despiece en caché (repetir hasta que falten 0)
```
- Abre el despiece de una moto de prueba de esa línea en el preview `tallerya` (`/garaje/…`) y mira con `read_page` (no capturas) que salgan las láminas con su dibujo propio y que «Toca ya» abra en la pieza.
- 10 piezas con tarea al azar a la skill `mecanico` (paso 7 de la skill principal).
- Si cambiaste código (lector, glosario, traductor): `P manage.py test --exclude-tag=lenta -v 1` y la lenta del despiece (`P manage.py test -v 1`).

## 8. Producción (pendiente del usuario)
- Hoy los códigos y descripciones viven solo en la base local (salen del PDF) y los planos en `media/`. **Falta decidir** si se exportan los datos de piezas al repo o se cargan en el servidor. No subas `media/` ni el PDF; el mapa sí va al repo.
