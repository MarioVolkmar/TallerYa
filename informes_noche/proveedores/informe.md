# Proveedores de servicios (opción C): informe

Sin commit. Rama `piloto`.

## Qué quedó
- **App nueva `proveedores`**: `Categoria` (nombre, singular, ícono, etiqueta del precio, campos propios, «aparece en Soy proveedor», orden) y `Proveedor` con los campos comunes (WhatsApp, teléfono, municipio de la sede, municipios que atiende, barrios, dirección, web, 24 h / abre-cierra / horario en texto, descripción, foto, precio desde + fuente, aliado + beneficio, lat/lng, estado por revisar/publicado/pausado, verificado, alta equipo/asistido/autoregistro, token, Ley 1581). Lo propio de cada categoría va en `extras` según `CAMPOS_EXTRA` (hoy: `vehiculo` para grúas y `agenda` para CDA). `EventoProveedor` cuenta los clics a WhatsApp y a llamar por día (sin datos personales).
- **Migración de datos**: `proveedores 0002` crea las categorías Grúas, CDA y SOAT y copia `talleres.Grua` y `tramites.CentroCDA`. Después `talleres 0024` y `tramites 0004` borran los modelos viejos (y sus admin). Ya se aplicó en `db.sqlite3` (5 proveedores: 3 grúas demo, 2 CDA).
- **Lo que ve el motero** (sin rediseño): Emergencias (grúas) y Técnico-mecánica (CDA) leen de `Proveedor.objects.publicados("grua"|"cda")`. Números con o sin 57 (`wa_numero`/`tel_numero`). Se suman las chapas «Verificada», «CDA verificado» y «Se puede reservar hora». Los clics se cuentan con `static/proveedores/clics.js` (sendBeacon).
- **Alta asistida**: Consola › Proveedores › «+ Nuevo proveedor» crea la ficha por revisar y lleva a una página con el enlace y el botón «Enviar por WhatsApp» (mensaje ya escrito). El proveedor corrige y aprueba en `/proveedores/ficha/<token>/` sin cuenta. El enlace vence a los 30 días; «Generar enlace nuevo» invalida el anterior.
- **«Soy proveedor»**: `/proveedores/unete/` (formulario corto, autorización obligatoria, 5 por hora por IP). Detrás del interruptor nuevo `proveedores_registro` (Consola › Configuración, **prendido por defecto**). Enlace en el pie solo sin sesión.
- **Consola**: sección «Proveedores» (ícono camión, contador de por revisar). Filtros por texto, categoría y estado; «+ Categoría»; tabla con menú «⋯» (Editar, Reenviar enlace, Pausar/Reactivar, Verificar, Ver reporte, Eliminar), píldora «Aprobar» y sello de verificado. Todo pasa por `consola.acciones` con bitácora. Editar registra el detalle campo por campo.

## Decisiones
- Precio: un solo campo `precio_desde` cuya etiqueta pone la categoría («Tarifa base desde», «Revisión de moto desde»), en vez de un campo por categoría.
- Lo cargado por el equipo con datos públicos (`origen_alta=equipo`) no espera la aprobación por enlace, igual que los talleres con cuenta. Lo asistido o autoregistrado no se publica sin la aprobación del proveedor.
- SOAT: la categoría queda creada y sin proveedores. La venta del SOAT (PedidoSoat) no se tocó.
- El reporte de cada proveedor sale en la misma sección (`?seccion=proveedores&reporte=<pk>`, reusa `reporte_detalle.html`). No hay ficha pública de proveedor: «Ver ficha pública» abre la edición.

## Pruebas
- `proveedores/tests.py`: 18 pruebas (modelo, migración, permisos, alta asistida, token vencido/renovado, autoregistro e interruptor, límite, filtros, acciones con bitácora, edición, categoría, clics y reporte). Se ajustaron las de grúas (`talleres/tests.py`) y CDA (`tramites/tests.py`) y PUBLICAS en `config/tests_seguridad.py`.
- Suite completa (`--parallel 1`): 993 pruebas. La única que falla es `domicilio.tests.AltaYVerificacionTests.test_eleccion_de_rol_ofrece_mecanico`, por `cuentas/registro_elegir.html`, que está editando otra sesión. No viene de este cambio.
- revisar-ux a 1280 y 375 px (Chrome sin ventana por CDP, script `ux_cdp.mjs` en el scratchpad de la sesión, porque el panel tiene sesión de otra cuenta). Sin bloqueantes propios: solo ruido conocido del sitio (barra de instalar, cabecera, `cs-btn-ok`). Arreglado: la lista de campos propios en «+ Categoría».

## Pendiente
- Volver a correr `manage.py test -v 1` cuando la sesión que toca `registro_elegir.html` termine.
- Mirar a ojo las capturas guardadas (`consola1280.png`, `ficha375.png` en el scratchpad de la sesión). No se revisaron por el tope de contexto.
- Más adelante (fuera de alcance): mostrar los puntos de SOAT al motero, ficha pública por proveedor, rediseño de Emergencias y Técnico-mecánica, editar y borrar categorías desde la consola (hoy solo crear y editar por URL `/consola/proveedores/categoria/<pk>/`, y borrar desde el admin).
