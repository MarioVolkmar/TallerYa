# Homogeneizar taller ↔ mecánico a domicilio

| Par (taller / mecánico) | Diferencia hallada | Mejor diseño | Estado |
|---|---|---|---|
| Panel | Ya iguales (Por hacer, franja, citas/visitas, reseñas) | taller | sin cambio |
| Citas / Solicitudes | Mecánico: sin barra de filtros, intro larga, botón «Registrar servicio» extra, item en tarjeta propia, vacío sin estructura | taller | **igualado** (volver a Mi panel, h1, `lt-filtros`, lista en `papel pt-caja`, vacío `pt-vacio`; quité el botón duplicado) |
| Servicios | Mecánico: franja solo si ya había servicios, título distinto, nota con otro margen | taller | **igualado** con parcial `talleres/_servicios_cabecera.html` (cifras, botón, nota); título «Servicios registrados» |
| Registrar servicio | Flujos distintos (placa/código vs visita) | — | diferencia real, sin cambio |
| Precios | Ya iguales (mismo editor y estado) | — | sin cambio |
| Cupones | Taller en el panel; mecánico en página propia | — | diferencia de estructura, sin cambio |
| Reseñas | Taller: resumen con reparto por estrellas y filtro; mecánico: solo nota | taller | **igualado** con parcial `talleres/_resenas_resumen.html` y filtro por estrellas en la vista |
| Perfil / editar | Ya casi iguales (Presentación, Especialidades, Garantía, Precios, Marcas, Fotos, barra de progreso, «Guardar perfil»). Taller volvía a Mi cuenta; mecánico a su panel | mecánico | **igualado** (taller vuelve a «Mi taller»); orden de secciones difiere solo por lo real: ubicación/horario/agenda (taller) y zonas/tarifa/urgencias/verificación (mecánico) |
| Ficha pública | Mecánico tiene zona/urgencias (real) | — | sin cambio |
| Registro | Cuenta nueva: ambos con pasos `rt-cabeza`, mismo título y botón. Taller con sesión (`talleres/registro.html`) usa hero corto; mecánico, pasos | — | sin cambio (flujo con sesión del taller queda aparte) |
| Mi cuenta, agenda/horario, estadísticas, registro | Taller tiene agenda y estadísticas propias; mecánico las lleva en el panel | — | diferencia real; sin cambio |

Archivos: `talleres/templates/talleres/_servicios_cabecera.html`, `_resenas_resumen.html` (nuevos); `servicios_taller.html`, `resenas_taller.html`; `domicilio/templates/domicilio/{servicios,solicitudes,resenas}.html`; `domicilio/vista_servicios.py`, `domicilio/views.py` (`resenas`); `tallerya.css` (`.pt-caja .vd-item`).

Verificación: pruebas `domicilio talleres` (331, sin lentas) OK. **Revisión visual 375/1280 NO hecha:** el navegador integrado bloqueó localhost y no pude leer la clave de `privado/cuentas-prueba.txt` para entrar.
Pendiente: revisión visual (la hará el usuario).
