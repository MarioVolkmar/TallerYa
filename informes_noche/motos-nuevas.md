# 7 motos nuevas en el catálogo (2026-11-15)

Catálogo pasa de 25 a **32 líneas**. Todo está en local: migración `garaje/migrations/0032_siete_lineas_nuevas.py` aplicada, despieces importados a la base local (las imágenes están en `media/`, que no va al repo). Sin commit.

## Resumen por moto

| Moto (línea en TallerYa) | Intervalos (`garaje/intervalos/`) | Catálogo (ficha) | Despiece (`despiece_mapas/`) | Qué falta |
|---|---|---|---|---|
| **Honda XR 190L** | `honda_xr_190l.json`, del manual del propietario Honda LatAm 2016. Aceite 6.000 km/1 año, filtro de aire 18.000, bujía 12.000, válvulas 6.000, cadena 1.000, líquido de frenos 2 años | enduro 184 cc, disco/tambor, mono, 19/17 | `honda_xr190l_2017.json`: XR190LH (13K79H01), 17 láminas, 377 partes | El manual es de 2016. El catálogo trae cuerpo de aceleración (FI): falta confirmar si la XR190L de Colombia es de carburador o de inyección |
| **Suzuki DR 150** (carburada) | `suzuki_dr_150.json`, del manual de servicio de Suzuki Colombia (tabla p. 2-1). Aceite 3.000 km/6 meses, filtro de aire 12.000/18 meses, bujía 10.000, válvulas 3.000, cadena 1.000, líquido 2 años | enduro 149 cc, disco/tambor, mono, 19/17 | `suzuki_dr150_fa403jc100.json`: FA403JC100 (2022), 24 láminas, 504 partes | **FI ABS**: no hay manual ni catálogo, así que no la agregué (rige la carburada). Tapón de drenaje sin enlazar: no se pudo confirmar cuál es en el catálogo |
| **Yamaha XTZ 150** | `yamaha_xtz_150.json`, del manual Incolmotos 2025 (escaneado; cuadro pp. 6-3 a 6-6 leído en imagen). Aceite 3.000, filtro de aceite 6.000, filtro de aire 6.000, bujía 6.000, válvulas 3.000, cadena 500, líquido 2 años | enduro 149 cc, disco/tambor, mono, 19/17 | `yamaha_xtz150_bbl1.json`: BBL1 (2019), 18 láminas, 381 partes | — |
| **TVS Raider 125** | `tvs_raider_125.json`, del manual Auteco FI 2025. Aceite 5.000, filtro de aire 10.000, bujía 10.000, válvulas 5.000, líquido 20.000, aceite de horquilla 20.000. Cadena **aproximada** (el cronograma solo la pide cada 5.000 km; rige la del plan general) | calle 125 cc, disco/tambor, mono, 17/17 | `tvs_raider125_my23.json`: MY23 **carburada**, 16 láminas, 379 partes | El catálogo es el MY23 de carburador y el manual es el FI de 2025. Falta la llanta delantera en el texto del catálogo (la copia de studocu perdió esas filas) |
| **Yamaha FZ 2.0** | `yamaha_fz_20.json`, del manual FZ-S FI V3.0 de Yamaha Argentina 2022 (mismas llantas y frenos que la B6U1). Aceite y filtro de aceite 3.000, filtro de aire 16.000, bujía 13.000 (luego cada 15.000), válvulas 3.000, cadena 500, líquido 2 años | calle 149 cc, disco/disco, mono, 17/17 | `yamaha_fz20_b6u1.json`: B6U1 (2019), 19 láminas, 414 partes | El manual es de Argentina, no de Colombia; vale la pena verificar con el de Incolmotos si aparece |
| **Hero Hunk 125R** | `hero_hunk_125r.json`, del manual de Hero Perú (may-2025). Aceite 6.000 (completar cada 3.000), filtro de aire 15.000, bujía 12.000 (luego cada 15.000), válvulas 3.000, cadena 1.000, kit de arrastre 20.000, líquido y aceite de horquilla 2 años/30.000 | calle 125 cc, disco/tambor (CBS), mono, 17/17 | `hero_hunk125r_2024.json`: CBS (dic-2024), 17 láminas, 325 partes | La copia de studocu del catálogo **está incompleta**: faltan freno delantero (F-4/F-8), bomba de aceite (E-6/E-7), batería y llantas. Hace falta el catálogo completo |
| **Bajaj Boxer CT 125** (marca "Auteco Bajaj", como la CT 100) | `auteco_bajaj_boxer_ct_125.json`, del manual de usuario y garantía de Grupo UMA (Boxer CT 125 Sport). Aceite 5.000/3 meses, filtro de aire 20.000, bujía 15.000, válvulas 5.000, cadena 500, bandas y pastillas 15.000 | calle 125 cc, **tambor/tambor**, doble amortiguador, 17/17 | `bajaj_boxer_ct125.json`: 18 láminas, 268 partes | El catálogo trae freno delantero de tambor y el manual (versión Sport) de disco: la ficha quedó con tambor, como el catálogo. Una anotación del cuadro dice "aceite cada 10.000, rellenar cada 5.000"; tomé 5.000, que es lo que marcan la tabla y la de lubricantes |

| **Hero Hunk 150** (2012; agregada después) | `hero_hunk_150.json`: **todo aproximado**. No hay manual de la Hunk 150, así que se toman los intervalos de la Hunk 125R (aceite 6.000, filtro de aire 15.000, bujía 12.000, válvulas 3.000, cadena 1.000, kit 20.000, líquido 2 años/30.000). Del catálogo de la 150 salen la bujía NGK CPR8EA-9, las llantas 2.75-18 y 100/90-18, la cadena 428H-120 y el piñón 14T / corona 43T. Las presiones de llanta son las de la 125R | calle 149 cc, disco/tambor (hay versión con disco atrás), **doble amortiguador**, 18/18 (migración `0033_hunk_150`) | `hero_hunk150_2012.json`: catálogo completo HCML Colombia ago-2012, versión de tambor, 20 láminas, 384 partes (con freno delantero, bomba de aceite, batería y llantas) | Manual del propietario de la Hunk 150 para cambiar las cifras aproximadas por las reales; tipo y cantidad de aceite. La Hunk 125R no se tocó: sigue con sus 17 láminas y sin piezas de la 2012 |

Fuente de cada cifra: el campo `fuente` de cada tarea en el JSON. Lo que no sale del manual quedó con `aproximado: true`: la cadena de la Raider y todas las tareas de la Hunk 150.

Con la Hunk 150 el catálogo queda en **33 líneas**.

## Cambios de código (todos en `garaje`)
- `despiece_lectores.py`:
  - Suzuki: ahora lee los códigos sin guiones de los catálogos nuevos (`59300H2JY10H000`). Sin esto, la DR150 perdía la mayoría de las piezas, entre ellas las pastillas.
  - Formato nuevo **`hero2`**: encabezado `E-2 : TÍTULO`, variantes `F-7-CBS`, códigos con cola de 5 caracteres, dibujo en la página anterior y recorte del blanco. Así no cambia la forma de leer los catálogos Honda y Hero que ya estaban.
  - **`quitar_marca_studocu()`**: las copias de studocu traen en cada página "Downloaded by <nombre> (<correo>)", un QR y un logo. El importador ahora los borra antes de dibujar las láminas (en memoria; el PDF no se toca). Revisé las 4 motos afectadas (XR190L, Raider, Hunk y Boxer): ya no quedan datos personales en las imágenes.
- `management/commands/importar_despiece.py`:
  - Auteco: en "FIGURA N°10" el número se leía como figura 0. Ya está corregido, y los 7 mapas Auteco existentes leen exactamente igual que antes (lo comparé).
  - `descripciones` del mapa: en los catálogos en español ahora corrige también el nombre visible. Lo usé para arreglar la ligadura "ti" rota ("AmorƟguador rasero" → "Amortiguador Trasero").
- Lector `hero` (para la Hunk 150): ahora lee bloques con letra o variante ("E-1A", "E-8A", "F-11-DRUM"). Cada letra suma 50 al número de figura ("E-8A" = 158) para no chocar con "E-8". También reconoce "Íntem de servicio" al recortar el dibujo. Los mapas Honda no cambian y la Eco Deluxe lee igual que antes (lo comparé).
- Migración `0033_hunk_150` (depende de la 0032).
- Migración `0032_siete_lineas_nuevas` (depende de `0031_servicio_taller`, de la sesión lado-taller).

## Modelo 3D (no tocado): base que conviene
El 3D elige rasgos por nombre (`moto3d/rasgos.js`, lista `LINEAS`) y, si no hay coincidencia, usa la familia según el tipo y el cilindraje.
- **XTZ 150**: ya toma los rasgos de la XTZ (`/xtz/`). Conviene revisar el rin delantero de 19".
- **Boxer CT 125**: ya toma los de la Boxer (`/boxer/`).
- **XR 190L** y **DR 150**: enduro genérica. Base sugerida: XR 150L para la XR190L, y XTZ 125/XR 150L para la DR150 (tanque más ancho, faro cuadrado).
- **Raider 125** y **Hunk 125R**: caen en "clásica" porque tienen menos de 150 cc, pero en realidad son naked. Base sugerida: la familia naked de la CR4 125 (o la Apache RTR 160 para la Raider).
- **Hunk 150**: cae en "clásica" (149 cc, calle). Base sugerida: naked de calle con doble amortiguador y rines de 18"; lo más cercano es la Discover 125 o la CB 125F, con tanque más grande y faro de naked.
- **FZ 2.0**: cae en "clásica" (149 cc). Base sugerida: los rasgos de la FZ 25 (`/fz\s*25/` no la reconoce) con familia naked.

## Pendiente para el usuario
- Hunk 125R: catálogo completo (la copia de studocu no trae varias láminas).
- DR150 FI ABS: manual y catálogo (Suzuki Motor de Colombia).
- Confirmar si la XR190L y la Raider que se venden hoy en Colombia son de carburador o de inyección (el despiece cargado es de la XR190L 2016 con inyección y de la Raider MY23 de carburador).
- Las láminas son imágenes de catálogos de fábrica: solo locales, igual que las de las otras 25 motos (sigue pendiente decidir cómo llevar los datos de piezas a producción).
