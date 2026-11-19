# TallerYa Ruta: integración y «Domiciliario verificado»

18 y 19-nov-2026 · copia principal, **sin commit**. Todo va detrás de `DOMICILIARIOS_ACTIVO`: con la bandera apagada, la página queda como antes, y hay pruebas que lo comprueban.

## Ronda 2 (19-nov): lo que pidió el usuario
1. **Fuera la marca «Atiende domiciliarios»** del directorio: el filtro, la insignia y la línea del descuento. El directorio quedó como estaba antes de Ruta.
   - `TallerAliado` queda solo como **descuento para domiciliarios verificados con Plus**. Se ve en Mi ruta y en la presentación, no en el directorio.
   - La migración `domiciliarios/0003` elimina `en_el_dia`, `horario_extendido` y `horario_texto`, vuelve obligatorio el descuento y borra los aliados que no tenían descuento.
2. **La moto sigue siendo lo principal.** La tarjeta grande de arriba pasó a ser una **franja compacta dentro de la agenda**, debajo de su título. La franja lleva:
   - pico y placa de hoy y mañana;
   - «Agenda con plan intensivo · ~km/día»;
   - el botón «Cerrar jornada» y el enlace «Mi ruta →»;
   - el interruptor.

   Va en la agenda porque esa es la sección que cambia con el plan intensivo. Si la moto no es de trabajo, solo queda el interruptor, en una línea discreta. El detalle completo está en `/domiciliarios/mi-ruta/`.
3. **La verificación pide exactamente 2 fotos, las dos obligatorias.** Ya no hay selfie ni niveles.
   - Las fotos:
     - el **pantallazo del perfil en la app**, donde se ve la placa o los datos de la moto;
     - la **foto de la moto con la placa visible**.
   - Además se elige con qué moto del garaje trabaja (solo motos con placa).
   - **Consola:** muestra lado a lado el pantallazo, la foto de la moto y la **placa del garaje** en grande, con el criterio «aprueba solo si las 3 placas coinciden». Trae motivos de rechazo sugeridos.
   - **Las fotos se vuelven a codificar al subirlas:** JPEG de máximo 1.600 px, sin EXIF (GPS, celular, fecha) y respetando la rotación. Hay una prueba de que el EXIF desaparece.
   - Se mantienen la autorización (Ley 1581), la carpeta privada, el acceso solo para el dueño y el staff, el borrado al decidir, la vigencia de 6 meses y la renovación por uso.
4. **UX en celular:**
   - **Verificación por pasos** (1 app y moto, 2 pantallazo, 3 foto de la moto, 4 autoriza y envía):
     - cada foto trae un dibujo de ejemplo y su lista de «✓ que se vea…»;
     - los botones de subir son grandes, con vista previa y el nombre del archivo;
     - en el celular, la foto de la moto abre la cámara;
     - el **estado** va arriba en una frase: «Estás verificado», «En revisión» (con las fotos enviadas y la opción «Retirar y borrar mis fotos»), «No pudimos verificarte» (con el motivo y el formulario para reintentar) o «Venció».
   - **Cierre de jornada:** va primero en Mi ruta.
     - Tiene un campo grande con «$» y 4 **montos de un toque**, calculados alrededor de lo que suele ganar.
     - Los km son opcionales y la gasolina va plegada en «Anotar gasolina».
     - El balance muestra primero «Te queda $X» en grande.
   - **Presentación:** se entiende en 5 segundos.
     - Título «Tu moto es tu trabajo.», 3 bloques (mantenimiento en días, cierre de jornada, pico y placa) y botones grandes.
     - Debajo: la tabla «el manual se queda corto», los precios y 3 pasos.
   - **Portada y registro:** los mismos 3 beneficios, con textos cortos y un botón de ancho completo en el celular. Se quitó «talleres que atienden en el día».

## Antes y después
Celular a 375–390 px; la consola, en escritorio. Las capturas salen de páginas reales renderizadas con el usuario demo. Para la consola se usó un staff temporal dentro de una transacción que se deshace, así que no queda nada en la base.

| | Antes | Después |
|---|---|---|
| Detalle de la moto | `ruta-integracion/antes-moto.jpg`: la tarjeta «Mi ruta» era lo primero, encima del 3D | `despues-moto.jpg`: franja dentro de la agenda; arriba siguen el 3D y el estado |
| Verificación | `antes-verificacion.jpg`: texto largo, niveles y selfie | `despues-verificacion-1.jpg` y `-2.jpg`: pasos con ejemplos. `despues-verificacion-pendiente.jpg`: estado claro |
| Mi ruta | `antes-mi-ruta.jpg`: formulario de 3 campos iguales | `despues-mi-ruta.jpg`: monto grande, montos de un toque y gasolina opcional |
| Consola | `antes-consola.jpg`: miniaturas pequeñas en una tabla | `despues-consola.jpg`: pantallazo, foto y placa del garaje lado a lado |

En el navegador no hay scroll horizontal en la moto, la verificación ni Mi ruta.

## Qué hay (resumen)
| Qué | Dónde |
|---|---|
| «Soy domiciliario» en el registro, también con Google. La cuenta queda con Ruta y su primera moto queda de trabajo. | `/cuenta/registro/` |
| Bloque breve «¿Trabajas en tu moto?» | Portada |
| Interruptor «La uso para trabajar». Con él, `calcular_plan` usa el plan intensivo con los km/día reales. | Moto, dentro de la agenda |
| Franja de la moto de trabajo. En las fallas frecuentes, cadena, frenos, llantas y clutch van primero. | Moto |
| Recuadro «¿Te varaste en ruta?» | `/mecanicos/` |
| «Mi ruta» en el menú. Aviso de pico y placa la noche anterior (`recordar_pico_placa`). Avisos de mantenimiento en días. | Menú y campana |
| Categoría «Domiciliarios» (`foro/0008`) | Foro |
| `Cupon.solo_domiciliarios` (`cupones/0005`), solo para verificados | Cupones |
| Verificación y cola de revisión con Bitácora y notificación | `/domiciliarios/verificacion/`, `/consola/?seccion=domiciliarios` |
| Vigencia de 182 días. Comando diario `revisar_verificaciones`: renueva sola con al menos 14 jornadas de 80 km/día de media en 30 días; si no, vence y pide fotos nuevas. Umbrales `RUTA_*` en settings. | Comando |

## Calidad
- **Suite completa:** 785 pruebas, OK, corrida después del último cambio.
- **Pruebas de Ruta** (54 en `domiciliarios`). Cubren:
  - las 2 fotos obligatorias y el EXIF quitado;
  - tipo y tamaño de archivo, moto ajena y autorización;
  - aprobar o rechazar con borrado de las fotos;
  - permisos: nadie ve las fotos de otro, sin staff no hay consola, nada por `/media/`;
  - renovación y vencimiento;
  - que la franja quede después del 3D y dentro de la agenda;
  - que el directorio no muestre la marca;
  - la bandera apagada.
- **`revisar-seguridad`** (código y autorización): 0 fallas. Los `FileField` están anotados en `permitidos.txt`.

## Ronda 3 (19-nov): pulido visto en computador
Capturas con el demo **sin placa, sin SOAT y sin verificar**, que es el caso de las capturas del usuario. Tomadas en computador (1200 px) y en celular (375 px).

| Parte | Antes | Después |
|---|---|---|
| Encabezado y tarjetas de Mi ruta | `antes2-mi-ruta-pc.jpg`, `antes2-mi-ruta-celular.jpg` | `despues2-mi-ruta-pc.jpg`, `despues2-mi-ruta-celular.jpg` |
| Resumen de la semana y del mes | `antes2-balance-pc.jpg` | `despues2-balance-pc.jpg` |
| Franja de la moto | `antes2-franja-pc.jpg`, `antes2-franja-celular.jpg` | `despues2-franja-pc.jpg`, `despues2-franja-celular.jpg` |

1. **Encabezado:**
   - «Ajustes» ahora es un botón secundario con ícono de engranaje, alineado con el título.
   - La moto va en una **ficha de chips**: moto (enlace, con ícono), km, km/día y, si aplica, «✓ Domiciliario verificado».
   - «Verifícate con 2 fotos» ahora es un **aviso** con ícono, texto corto y botón «Verificarme». Si la solicitud está en revisión, el aviso dice eso y el botón es «Ver solicitud». Cuando ya está verificado, el aviso no aparece.
2. **Tarjetas de arriba:** cada una es **clicable entera** y lleva su acción abajo con el mismo estilo:
   - Pico y placa: «Agregar placa →», o «Ver semana →» si ya tiene placa.
   - Mantenimiento: «Ver agenda →».
   - SOAT y técnico-mecánica: «Registrar fecha →» si no tienen fecha, «Renovar →» si están vencidos o por vencer, «Ver →» si están al día.
   - «Agregar placa» y «Registrar fecha» llevan a editar la moto.
3. **Resumen de la semana y del mes:** «Gastos: Gastos y consumo.» pasó a ser un botón «Ver gastos y consumo →».
4. **Franja «Moto de trabajo»:**
   - Los botones `.btn` de Ruta no tenían relleno, así que «Cerrar jornada» quedaba pegado al borde y se cortaba en computador. Ahora tienen relleno, interlineado y espaciado de letras; el texto ya no se desborda ni en computador ni a 375 px.
   - «Mi ruta →» es un botón secundario.
   - Sin placa, en lugar de «—» sale «Agrega la placa para ver tu pico y placa de hoy y mañana» con el botón «Agregar placa». Si falta la rotación vigente, lo dice.
   - En el celular los dos botones van a lo ancho, uno debajo del otro.
- **Pruebas:** nueva `AccionesSinDatosTests`, que revisa las acciones sin placa ni SOAT y la franja.

## Ronda 4 (19-nov): fuera el aviso punteado del garaje
- Quité de `/garaje/` el aviso con borde punteado «Mi ruta · tu jornada…». Se borraron la etiqueta `{% aviso_domiciliarios %}`, su plantilla `_aviso.html` y su CSS, porque ya no los usa ninguna página.
- En la lista de motos, la moto de trabajo lleva una **chapa pequeña «Trabajo»** sobre el borde superior de su tarjeta, y lleva a Mi ruta. Va fuera del enlace de la tarjeta (sin enlaces anidados), se esconde en el modo «Editar» y solo aparece con la bandera prendida.
- Si alguien tiene Ruta pero ninguna moto marcada, no se muestra nada en el garaje. El interruptor «La uso para trabajar» sigue en la agenda de cada moto: es lo más limpio.
- No quedan otros avisos punteados de Ruta. La línea del interruptor era punteada y pasó a línea sólida. Solo siguen punteados los botones de subir foto de la verificación, a propósito, porque son zonas de carga.
- **Capturas:** `despues3-garaje-pc.jpg` y `despues3-garaje-celular.jpg` (375 px). El «antes» es la captura que mandó el usuario.
- **Pruebas:** `test_mi_garaje_sin_aviso_y_chapa_en_la_moto_de_trabajo`. La prueba con la bandera apagada revisa que no salga la chapa.

## Ronda 5 (19-nov): verificación visible, chapa que acompaña a la tarjeta y modo Editar
1. **Chapa del estado de la verificación** (componente `_chapa_verif.html`), junto al título «Moto de trabajo» de la franja y en la ficha de Mi ruta:
   - **Sin verificar:** gris, con escudo vacío. Es un enlace a `/domiciliarios/verificacion/` con el título «Verifícate con 2 fotos para la insignia y los descuentos Plus».
   - **En revisión:** mostaza, escudo con reloj.
   - **Verificado:** verde, escudo lleno con la marca de verificación.

   Es pequeña (0,72 rem) para no competir con «Cerrar jornada». En Mi ruta, el aviso con el botón «Verificarme» sigue apareciendo solo mientras no esté verificado.
2. **La chapa «Trabajo» se mueve con la tarjeta del garaje:**
   - Usa el mismo desplazamiento (−2, −3 px) y el mismo tiempo (0,2 s) que `.tarjeta:hover`, con `.moto-ficha:has(...)`.
   - Funciona con el cursor o el foco en la tarjeta y también en la chapa: en ese caso la tarjeta se eleva con ella.
   - Con `prefers-reduced-motion` no hay transición.
   - En el celular no hay hover, así que las dos quedan quietas.
   - Comprobado en el navegador con el `transform` calculado: los dos elementos dan `matrix(1,0,0,1,-2,-3)`.
3. **Modo «Editar» del garaje:** el interruptor «La uso para trabajar» (`role="switch"`, 44 px de alto) va **dentro de la tarjeta**, en una barra de edición abajo, separada por una línea fina. El interruptor queda a la izquierda y «Eliminar» a la derecha, con el mismo centro vertical (medido en computador y a 375 px, sin choque).
   - Los dos controles van con posición absoluta sobre la tarjeta y fuera de su enlace, para no anidar controles en un `<a>`. En el modo Editar la tarjeta deja de elevarse con el hover.
   - Sin Ruta (sin interruptor), «Eliminar» sigue arriba a la derecha, como antes.
   - Marca o desmarca la moto de trabajo sin entrar a la moto y vuelve a la lista. La vuelta usa un valor fijo (`volver=garaje`), así que no puede usarse como redirección abierta.
   - Marcar otra moto la pasa a ser la de trabajo.
   - Solo aparece con la bandera prendida.
- **Capturas:** `despues4-franja-pc.jpg`, `despues4-franja-celular.jpg`, `despues4-garaje-pc.jpg`, `despues4-garaje-editar-pc.jpg` y `despues4-garaje-editar-celular.jpg` (375 px).
- **Pruebas:** `ChapasYModoEditarTests` (los 3 estados de la chapa, el interruptor en el modo Editar, la vuelta al garaje y que no haya redirección abierta). Las 172 pruebas de domiciliarios y garaje pasan.

## Extra: talleres con servicio a domicilio (19-nov)
Esto no depende de la bandera de Ruta: es del directorio. Se usa el modelo que ya existía, `domicilio.TallerDomicilio`, con sus zonas, servicios, tarifa y urgencias.
- **Filtro «Va a domicilio»** en el directorio (`?domicilio=1`), junto a «Solo verificados» y «Con cupón».
  - Aparece en los chips de filtros activos.
  - Funciona con la búsqueda, el orden y la paginación (los enlaces de página conservan el filtro) y en las páginas SEO por barrio y por servicio.
  - Usa el mismo criterio que `/mecanicos/`: servicio activo y taller aprobado, así que los talleres inactivos no salen.
  - Con el filtro puesto, el directorio enlaza a los mecánicos independientes.
- **Panel del taller:** el enlace «¿Vas a domicilio?» pasó a ser un **interruptor de un toque** (`domicilio:alternar_taller`, POST, solo el propio taller). Si lo prende y no tiene zonas, lo lleva a elegirlas en `/mecanicos/mi-taller/`. Si ya tiene zonas, muestra «N zonas» con un enlace para editarlas.
- **Detalle del taller:** ya mostraba la insignia «🛵 Va a domicilio», las zonas, la tarifa y si atiende urgencias. Se dejó igual.
- **Captura:** `ruta-integracion/directorio-va-a-domicilio.jpg` (celular a 390 px, con el chip del filtro activo y la chapa en cada tarjeta).
- **Pruebas:** 6 en `talleres/tests_filtro_domicilio.py`. Cubren:
  - el filtro con talleres apagados, sin configurar e inactivos;
  - la búsqueda, el orden y la paginación;
  - las páginas SEO;
  - la coherencia con `/mecanicos/`;
  - el interruptor (prender y apagar, solo POST, solo el propio taller).

## Pendientes
- **Menú (lo hace la sesión «Menú: reorganizar la navegación»; aquí ya no se toca `base.html`):** hoy «Mi ruta» está en la barra superior y en el menú del celular, con `{% load domiciliarios_tags %}{% ruta_menu as mi_ruta %}`. `ruta_menu` devuelve True solo con la bandera prendida y si el usuario tiene TallerYa Ruta (una consulta por petición). Esa sesión va a reubicar el enlace en «Mi garaje» y en el menú de la foto; la URL es `{% url 'domiciliarios:panel' %}`.
- Programar `revisar_verificaciones` a diario en el cron.
- Confirmación en un taller aliado con PIN y código de flota: solo anotados.
- Falta la casilla «solo domiciliarios» en el formulario de cupones del taller. Hoy se marca en el admin.
- Los descuentos de talleres se cargan en el admin («Descuentos de talleres para domiciliarios»). No hay pantalla para que el taller los ofrezca él mismo.
- Cada perfil tiene una sola moto de trabajo.
