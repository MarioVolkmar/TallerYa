# Relevo — Diseño general (portada, base.html, cuentas/templates, trámites)

## Hecho (sin commit)
- Moto detalle más rápido: caché "despiece" (base + capa de estado por request), SVG en caché; señal en garaje/apps.py sube "generacion". Optimización movió despiece a DatabaseCache y SVG a "despiece_svg".
- App `tramites`: TarifaSoat (tarifas oficiales 2026 Fasecolda), CentroCDA (2 CDA reales, no aliados), PedidoSoat con flujo simulado (pagos.py, `SOAT_PAGO_SIMULADO`), admin con cola, notificaciones, fija soat_vence. Migraciones 0001–0003. Abierto a visitantes.
- Páginas: soat.html ("Pide tu SOAT"), tecnomecanica.html (tarjetas CDA con mapa 39 %, "Talleres que te ayudan").
- Avisos SOAT/técnico compactos que llevan a trámites (garaje/avisos.py).
- Diagnóstico: toggle cambios/automática, resumen estilizado, chip de moto con apodo, tarjetas taller opción B.
- Insignias con emoji (Viajero 🛵), cupones por puntos (cargar_cupones_puntos, en cargar_demo).
- Panel taller: botones en grid parejo; "Ir al foro" como pill.
- Portada: secciones 03 Trámites y 04 Comunidad, botón "¿Te varaste?", botón día/noche del carrusel 3D (Auxiliares añadió `.portada-controles + .portada-noche`: conservar).
- base.html: menú "Papeles" (parciales/menu_servicios.html, tipografía = nav-link), Diagnóstico, pill emergencias, footer; navbar sin desborde (clases nav-c1..3 / nav-hamburguesa por JS). Verificado 1024–1920 px y zoom 125 %.
- Mi cuenta: "01 Mis citas" (cuentas/citas.py: detalle, cancelar, .ics) + insignias.
- Última suite propia: 366 OK.

## Pendiente
- Usuario: configurar Google OAuth, SMTP, WhatsApp Business; en Render `migrate` + `createcachetable`.
- No verificado visualmente: grid de botones del panel taller y pills pt-enlace.
- Prueba de notificaciones falla por aceite NMAX 6.000 km (no es mía).

## Archivos clave
tramites/*, templates/base.html, templates/parciales/menu_servicios.html, talleres/templates/talleres/inicio.html, talleres/views.py (_comunidad_portada), cuentas/citas.py, cuentas/templates/cuentas/{mi_cuenta,_mis_citas,cita_detalle}.html, garaje/vista_diagnostico.py + diagnostico.html, talleres/static/talleres/css/tallerya.css (bloques tr-, tp-, cm-, dt-, diag-, ns-, nav-c*, portada-noche).
