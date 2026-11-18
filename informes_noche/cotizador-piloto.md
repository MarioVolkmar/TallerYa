# Piloto del cotizador de repuestos — informe (18-nov-2026)

Rama `claude/piloto-cotizador-5cb845` (worktree propio). **No está unida a main.** Apagado por defecto.

## En corto
- Hay un botón **«Cotizar»** en la ficha de cada pieza del despiece y junto a cada repuesto de «Qué necesitas» en
  el plan de mantenimiento. Al pulsarlo sale un recuadro con el rango (mínimo a máximo), el precio más común
  (mediana), hasta 5 vendedores con enlace y ciudad, la fecha de la consulta y el aviso de que los precios son
  orientativos.
- **Mercado Libre exige token desde 2025.** Probado hoy: toda búsqueda anónima responde 403. Mientras no se
  registre la aplicación, el piloto muestra **precios de ejemplo** con un aviso amarillo bien visible. Por eso
  **no se pudo medir la calidad real de los resultados** (ver abajo qué sí se probó).
- Todo va en la app `cotizador`. Fuera de ella solo hay 9 líneas: 4 en `config/` y 2 ganchos en 2 plantillas.

## Qué se hizo
| Pieza | Archivo |
|---|---|
| Bandera `COTIZADOR_ACTIVO` (entorno, apagada por defecto) y app en `INSTALLED_APPS` | `config/settings.py` (+4 líneas) |
| `path("cotizador/", include(...))` | `config/urls.py` (+1) |
| Gancho 1: CSS y JS del cotizador | `garaje/templates/garaje/moto.html` (`{% cotizador_script %}`) |
| Gancho 2: botón en «Qué necesitas» | `garaje/templates/garaje/_tarea.html` (`{% cotizador_boton r.codigo %}`) |
| Consulta a Mercado Libre (MCO), token con renovación automática | `cotizador/fuentes/mercadolibre.py` |
| Precios de ejemplo sin credenciales (con basura a propósito) | `cotizador/fuentes/ejemplo.py` |
| Filtro: basura, otra pieza, otra moto, precios atípicos | `cotizador/filtro.py` |
| Caché de 24 h, máximo 2 consultas por cotización | `cotizador/servicio.py`, modelo `Cotizacion` |
| Vistas `/cotizador/parte/<id>/` y `/cotizador/codigo/?c=` | `cotizador/views.py` |
| Comando para el cron | `manage.py refrescar_cotizaciones --max 60` |
| Admin de solo lectura de las cotizaciones | `cotizador/admin.py` |
| Guía de token, cron y reversión | `cotizador/README.md` |

Con la bandera apagada, las etiquetas no pintan nada (ni un salto de línea) y las vistas responden 404. Hay una
prueba que lo comprueba.

**Consulta.** Primero la referencia del despiece con la moto (`2DP-F5805-00 NMAX 155`). Si eso deja menos de 3
resultados buenos, se intenta con el nombre (`Pastillas de freno Yamaha NMAX 155`). A Mercado Libre solo va ese
texto: nada del usuario. La llamada sale del servidor con `urllib`, sin cookies. El navegador nunca habla con
Mercado Libre, así que la CSP de `config/cabeceras.py` no cambió (en el navegador: 0 peticiones a Mercado Libre).

**Filtro** (`cotizador/filtro.py`), en este orden:
1. Palabras de no-repuesto: llavero, calcomanía, juguete, lote, mayorista, «para carro»…
2. Debe aparecer la primera palabra con sentido de la pieza (o un sinónimo), salvo que el título traiga el código
   exacto.
3. Se descarta si nombra otra línea de moto y no la nuestra.
4. Precios atípicos: fuera de mediana × [0,35 – 2,8] y de las vallas de Tukey.

Lo compatible (código o línea en el título) va primero.

**Frenos.** Se reutiliza `cuentas/limites.py`:
- 40 cotizaciones por hora y persona;
- 80 por IP;
- un tope global de 300 consultas nuevas por hora, que cuida la cuota de Mercado Libre.

Si la fuente falla, se muestra el último dato guardado con su fecha.

**Celular.** Probado a 375 px: el recuadro cabe sin desbordar (`scrollWidth` = 375) y no hubo errores de consola.
La captura es `informes_noche/cotizador-piloto-captura.jpg`.

## Cómo probarlo
```
set DJANGO_DEBUG=1
set COTIZADOR_ACTIVO=1
venv\Scripts\python.exe manage.py migrate cotizador
venv\Scripts\python.exe manage.py runserver 8011
```
Abrir una moto con despiece, elegir una pieza y pulsar «Cotizar». También se puede abrir una tarea del plan y
usar el «Cotizar» de «Qué necesitas». Sin token, sale «Precios de ejemplo».

Pruebas:
- `manage.py test cotizador -v 1`: 12 pruebas, todas con la red simulada.
- Suite rápida (`--exclude-tag=lenta`): **607 pruebas, OK** (25 s).

En este worktree (no tiene `.env`) hay que anteponer `DJANGO_DEBUG=1`.

## Calidad de los resultados (prueba real del 18-nov-2026)
**Contra Mercado Libre sin token**, con `/sites/MCO/search` y 5 consultas: el código de las pastillas NMAX,
pastillas NMAX, kit de arrastre NS 200, filtro de aceite NMAX y bujía NKD. **Las 5 dieron 403.**
`/products/search` (el buscador documentado hoy) también da 403. **No hay precios reales que evaluar hasta tener
el token.**

Lo que sí respondió sin token es el predictor de categoría (`/sites/MCO/domain_discovery/search`):

| Consulta | Categoría que predijo | ¿Bien? |
|---|---|---|
| `2DP-F5805-00 NMAX 155` (código) | Repuestos para motos → *Sensores* | No |
| pastillas de freno Yamaha NMAX 155 | Pastillas de freno | Sí |
| kit de arrastre Bajaj Pulsar NS 200 | Kits de arrastre para motos | Sí |
| filtro de aceite Yamaha NMAX 155 | Filtros de aceite | Sí |
| bujía AKT NKD 125 | Bujías | Sí |

Lectura: el nombre de la pieza más la moto ubica bien la categoría (4 de 4). El código solo no la ubica, porque
los vendedores casi nunca ponen el código Yamaha en el título. Sospecha razonable: con token, muchas consultas
por código traerán pocos resultados y entrará el respaldo por nombre (ya programado).

**Filtro, con datos simulados realistas** (prueba `FiltroTests`): de 8 publicaciones de «pastillas NMAX» quedaron
las 4 correctas. Salieron:
- un llavero (basura);
- un disco de freno (otra pieza);
- unas pastillas de Pulsar NS 200 (otra moto);
- unas de $950.000 (precio atípico).

Rango resultante: $39.000 a $48.000, típico $43.500.

**Precios de ejemplo** (lo que se ve hoy sin token): pastillas NMAX entre $33.600 y $55.600, filtro de aceite
entre $13.400 y $28.700. En cada uno se filtran 3 elementos de basura puestos a propósito. Son números inventados
y la interfaz lo dice.

## ¿Mercado Libre exige token? Sí
- La documentación oficial (developers.mercadolibre.com.co, «Ítems y Búsquedas», actualizada el 10/09/2026) ya
  solo muestra `/sites/$SITE_ID/search` filtrando por vendedor y siempre con `Authorization: Bearer`. La búsqueda
  libre documentada es `/products/search?site_id=MCO&q=…` (catálogo, acepta part number), también con Bearer.
- «Autenticación y Autorización»:
  - el access token dura 6 h;
  - el refresh token es de un solo uso y dura 6 meses;
  - el token se envía por cabecera.
- El código intenta primero `/sites/MCO/search?q=` con token. Si da 403 o 404, usa `/products/search` y las
  publicaciones de cada producto.

**Cómo obtenerlo** (pasos completos en `cotizador/README.md`):
1. Crear una aplicación en el DevCenter con una cuenta de Mercado Libre. Lo debe hacer el usuario: no creé
   cuentas ni aplicaciones.
2. Autorizarla una vez para obtener un `code`.
3. Cambiar el `code` por tokens con `curl`.
4. Poner `ML_APP_ID`, `ML_SECRET` y `ML_REFRESH_TOKEN` en Render.

Al primer uso se renueva solo y guarda el refresh token nuevo en su tabla.

## Costos
- **Interfaz de Mercado Libre: gratis** (no cobra por consultar). Tiene límites de uso por aplicación que no
  están publicados. Para cuidarlos están la caché de 24 h (una pieza se consulta como mucho una vez al día, la
  pidan 1 o 100 personas), el tope de 300 consultas nuevas por hora y el de 60 piezas por corrida del cron.
- **Base de datos:** unos 2 KB por cotización. Mil piezas ocupan unos 2 MB; cabe de sobra en el plan actual.
- **Cron nocturno:** en Render, un cron job se cobra aparte (según su página de precios, por minuto con un mínimo
  de alrededor de 1 US$ al mes; verificarlo al activarlo). Alternativa gratis: llamarlo desde GitHub Actions como
  ya se hace con `/tareas/avisos/`. Hace falta un endpoint con `TAREAS_TOKEN`; queda para la fase 2.
- **Sin cron también funciona:** cada pieza se refresca sola cuando alguien la pide y el dato tiene más de 24 h.

## Reversión (3 pasos)
1. **Apagar la bandera:** quitar `COTIZADOR_ACTIVO` del entorno (o ponerla en `0`). La página queda exactamente
   igual que antes.
2. **Quitar la app:** si nunca se unió, no hacer nada (vive solo en esta rama). Si se unió, `git revert` de los
   commits del piloto. A mano:
   - borrar `cotizador/`;
   - quitar su línea en `INSTALLED_APPS` y `COTIZADOR_ACTIVO` en `config/settings.py`;
   - quitar el `include` en `config/urls.py`;
   - en `moto.html` y `_tarea.html`, quitar `cotizador` del `{% load %}` y las etiquetas `{% cotizador_script %}`
     y `{% cotizador_boton r.codigo %}`.
3. **Deshacer su migración** *antes* de borrar la carpeta: `manage.py migrate cotizador zero`. Borra solo sus 2
   tablas (`cotizador_cotizacion`, `cotizador_tokenmercadolibre`); no hay claves foráneas hacia otras apps.

## Fase 2 sugerida
1. **Token y medición real.** Registrar la app y repetir la prueba con 20 piezas de 3 motos, contando cuántos
   resultados buenos hay por consulta. Con eso se ajustan las palabras del filtro y los sinónimos.
2. **Usar la categoría.** El predictor `domain_discovery` funciona sin token y acierta con el nombre de la pieza:
   filtrar por `category_id` quitaría casi toda la basura antes del filtro de texto.
3. **Almacenes aliados.** Una tabla `PrecioAliado` (almacén, código, precio, fecha) que el almacén carga desde la
   consola o con un CSV. Se mostraría primero, con «Disponible en Medellín» y WhatsApp. Es el valor propio frente
   a Mercado Libre y abre ingresos (almacén destacado).
4. **IA cuando no hay resultados.** Si después de las dos consultas quedan menos de 3 resultados, un modelo con
   búsqueda web podría proponer equivalencias (otra referencia compatible o la medida estándar, p. ej. la bujía
   CPR8EA-9). Siempre marcado como «sugerencia», nunca como precio.
5. **Cron gratis** con GitHub Actions y un endpoint protegido con `TAREAS_TOKEN`.
6. Historial de precios (una fila por día) para mostrar «subió / bajó» y alertas de precio.

## Notas
- Las pruebas no llaman a internet (mock de `mercadolibre._pedir`).
- El servidor de demo usó una base temporal en el scratchpad de la sesión con datos propios de demostración: una
  NMAX con 4 piezas y códigos ilustrativos. No se tocó `C:\dev\TallerYa\db.sqlite3`.
- Al ejecutar un comando sin `DATABASE_URL`, Django pudo crear un `db.sqlite3` vacío dentro del worktree. Está en
  `.gitignore` y no va en el commit; se puede borrar con el worktree.
