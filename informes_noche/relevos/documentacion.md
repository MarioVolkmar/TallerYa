# Relevo — sesión Documentación y plan de negocio (2026-11-15)

## Hecho (todo verificado contra el código, sin commit)
- README.md: apps (incluye tramites y logros), instalación, pruebas, comandos de manage.py (incluye avisar_vencimientos, recordar_citas, evaluar_logros, precalentar_despiece), variables de entorno, Render, cron.
- docs/funciones.md: guía de las 10 funciones, más "Dónde está cada cosa", Extra SOAT (pago simulado, visitantes ven el precio sin cuenta), Mis citas y "Plan de mantenimiento por moto" (garaje/intervalos/*.json, 9 motos, null = general, 0 = sin límite, fuente única garaje/intervalos.py).
- docs/despiece.md: flujo catálogo → mapa → importador → dibujos → visor. Incluye:
  - cobertura: 25 líneas y 26 catálogos (la Gixxer 150 tiene 2 versiones; solo la de 2020 está activa; `Despiece.para()` elige por año entre los activos);
  - Aerox 155 (migración 0022);
  - filtro de aire por tipo;
  - "6. Caché" (alias despiece, precalentar_despiece, .github/workflows/despiece.yml).
- docs/datos/pico_placa_y_vencimientos.md y docs/datos/precios_referencia.md: datos con fuentes, fechas y nivel de confianza.
- Docstrings de módulo en 14 archivos (admin/urls/views/models de cuentas, cupones, foro y notificaciones, más garaje_extras y talleres/utils).
- Plan de negocio en un Claude Doc, "TallerYa — Plan de negocio y producto" (artifact BjywKCeCZuP2Ae3a7gjyUp):
  - fila Plus taller a $49.900/mes (supuesto);
  - bloque gratis vs Plus;
  - meta de 1 de cada 5 talleres;
  - validación con 10 entrevistas.
  Varias cifras son supuestos marcados.

## Pendiente
- Commit de la documentación: lo decide el usuario. Auxiliares propone hacer los commits juntos y por tema. Agregar rutas una por una, sin informes_noche/.
- Seguir actualizando docs/funciones.md y docs/despiece.md cuando otras sesiones avisen cambios (verificar en el código primero).
- Plan de negocio: reemplazar los supuestos por datos reales del fundador. Posibles entregables siguientes: pitch deck, modelo financiero, postulación a Capital Semilla / Ruta N.
- Datos: la mano de obra de kit de arrastre y de llantas no tiene cifras ("sin datos"). La multa de pico y placa tiene confianza baja. La fecha de fin de la rotación 2026-2 está sin decreto.

## Archivos clave
README.md · docs/funciones.md · docs/despiece.md · docs/datos/*.md · informes_noche/documentacion.md
