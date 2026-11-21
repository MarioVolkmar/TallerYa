# Piloto, paso 1 (rama `piloto`, sin commit)

Estado: código y pruebas listos; **faltan capturas PNG y la skill `revisar-ux`** (el navegador del panel negó abrir localhost:8002).

## Hecho
1. **Interruptor** `PILOTO_OCULTAR_SOCIAL` (env, por defecto activo; apagado al correr `manage.py test`). `config/piloto.py`: middleware que da 404 en `/foro/`, `/plus/`, `/r/`, `/cuenta/regalo/` y procesador de contexto `oculta_social`. Plantillas envueltas en `{% if not oculta_social %}`: menú Comunidad, Plus (menú, pie, mi cuenta, cupón exclusivo), Rodadas, foro en portada/bienvenida/inicio_taller/fallas, «Mis preguntas», «Invita y gana» (invita.html, cupones/lista), `data-foro` del chat. Sin borrar código.
2. **Medición**: ya existía (`EventoDiario`: visita/whatsapp/llamada por taller y día, sin datos personales; `ir_whatsapp`/`ir_llamar` cuentan el clic). No hizo falta modelo ni migración. Nuevo **reporte mensual por taller** en `/consola/?seccion=reportes` (selector de mes, totales).
3. **WhatsApp con mensaje**: `Taller.whatsapp_con_mensaje(moto, servicio)`; `ir` arma «Hola X, te encontré en TallerYa. Tengo una <moto> y necesito: <servicio>.» con la primera moto del usuario y `?servicio=<id>` (solo servicios del taller). El botón del perfil pasa `?servicio=` si viene en la URL. El clic se mide igual.

## Pruebas
Nuevas: `config/tests_piloto.py` (11). Suite rápida: 833 pruebas OK.

## Archivos
Nuevos: config/piloto.py, config/tests_piloto.py, consola/vistas/reportes.py, consola/templates/consola/reportes.html.
Editados: config/settings.py, consola/secciones.py, consola/tests.py (reportes ya no es «fase 2»), talleres/models.py, talleres/views.py, talleres/templates/talleres/{detalle,inicio,inicio_taller}.html, templates/base.html, templates/parciales/invita.html, cuentas/templates/cuentas/mi_cuenta.html, cupones/templates/cupones/{lista,obtener}.html, garaje/templates/garaje/{bienvenida,_fallas_frecuentes}.html, ayuda/templates/ayuda/_chispa_chat.html.

## Pendiente
Capturas hechas con Chrome sin ventana: reporte_consola_{1280,375}.png y perfil_taller_{1280,375}.png (la «1280» está tomada a 900 px de ancho). revisar-ux: sin desbordes, sin enlaces a foro/Plus, botón WhatsApp ≥47 px, 0 errores de consola; tabla del reporte compactada para caber a 375 px. La sesión inyectada ya se borró de db.sqlite3.

## Ajuste: precios solo de mano de obra con interruptor por taller
- `Taller.mostrar_precios` (default False; migración `0021_mostrar_precios`). Editable en la consola (Talleres › «Mostrar/Ocultar precios», queda en la bitácora) y en el panel del taller (Editar perfil).
- Perfil: encendido, «Mano de obra desde · Solo mano de obra, sin repuestos»; apagado, los servicios salen como chips y aparece «Cotiza por WhatsApp» con el botón del paso 1 (medido).
- Capturas 375 px: `precios_apagado_375.png`, `precios_encendido_375.png`. Suite rápida: 836 OK.
- Nota: los datos ya guardados no se filtran por «repuestos»; el texto del perfil y del panel dice mano de obra, y los talleres deben publicar rangos de mano de obra.
