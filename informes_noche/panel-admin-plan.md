# Consola de administración — estado y plan de la fase 2

Entrada: `/consola/` (enlace «Consola» en la cabecera y en el menú del celular, solo para el rol administrador = cuenta `is_staff` activa).
App: `consola/`. El admin de Django (`/admin/`) y la página vieja `/cuenta/administracion/` siguen igual y aparte.

## Fase 1 (hecha)

| Pieza | Dónde |
|---|---|
| Secciones declarativas (`key`, `label`, `icon`, vista, `badge`) | `consola/secciones.py` → `SECCIONES` |
| Página única `?seccion=` (recargar, compartir, atrás/adelante) | `consola/views.py::consola` |
| Acceso solo administrador en cada vista y acción | `consola/permisos.py::solo_admin` |
| Acciones: decorador `@accion` + vista única `ejecutar` (permiso → transacción → bitácora → respuesta JSON o redirección) | `consola/acciones.py`, `consola/views.py::ejecutar` |
| Bitácora con frase legible y detalle campo por campo | `consola/models.py::Bitacora`, sección `bitacora` |
| Eliminación segura con reglas `Dependencia` + Collector de Django (PROTECT) | `consola/eliminacion.py`, reglas en `consola/vistas/usuarios.py` |
| Límites de validación compartidos formulario ↔ plantilla | `consola/limites.py`, etiqueta `{% limite "campo" %}` |
| Reloj central (`reloj.ahora()`, `reloj.hoy()`, `with reloj.fijar(...)`) | `consola/reloj.py` |
| Confirmación, ocupado, avisos (toasts), tema claro/oscuro | `consola/static/consola/consola.js` y `.css` |
| Usuarios: búsqueda, rol, activar/desactivar, nombre y correo, contraseña temporal, eliminar, ficha | `consola/vistas/usuarios.py` |

Agregar una sección = una línea en `SECCIONES` + un módulo en `consola/vistas/` con `seccion(request) -> (plantilla, contexto)`.
Agregar una acción = una función con `@accion(clave, modelo=..., campos=..., frase=...)`; la bitácora y el permiso salen solos.

Notas de la fase 1:
- «Restablecer contraseña» crea una contraseña temporal que se muestra una sola vez (el SMTP aún no está configurado). Cuando haya correo, agregar la acción «enviar enlace» con el `RecuperarView` existente.
- El rol se deriva (staff / taller vinculado / perfil de motero): pasar a Taller exige elegir un taller sin cuenta; pasar a Motero exige que ya tenga perfil de motero (celular).
- Protecciones: nadie se quita a sí mismo el rol, ni se desactiva ni se borra; no se puede dejar al sistema sin administrador activo; solo un superusuario toca a otro superusuario.

## Fase 2

**Construido (versión mínima útil, 16-nov-2026):** Talleres (publicar/despublicar, verificar, eliminar seguro), Citas (filtros por estado y fechas, cancelar con motivo), Cupones (vigentes/vencidos/desactivados, activar/desactivar, eliminar seguro) y Moderación (reportes, preguntas, respuestas y reseñas: ocultar/mostrar, eliminar seguro, marcar revisado). Todo con @accion → bitácora. Fábricas `interruptor()` y `eliminador()` en `consola/acciones.py`. Datos demo: `manage.py sembrar_demo` (clave de las cuentas fijas en TALLERYA_CLAVE_PRUEBA o privado/cuentas-prueba.txt). Lo que sigue abajo y no está en esa lista sigue planificado.

Las insignias de pendientes ya cuentan datos reales: talleres sin aprobar, citas pendientes, solicitudes Plus, reportes del foro sin revisar.

### Resumen — aplica
- KPI: cuentas nuevas (7/30 días), talleres publicados vs. por aprobar, citas por estado, motos registradas, Plus activos, códigos de cupón canjeados.
- Actividad: últimas 10 entradas de la Bitácora + últimas cuentas y citas.
- Atención: lo mismo que las insignias, con enlace directo a cada sección.
- Todo con `reloj.hoy()` para poder probar con fechas fijas.

### Talleres — aplica (prioridad 1)
- Entidad: `talleres.Taller` (`activo`, `verificado`, `destacado`, `usuario`).
- Aprobar (= `activo=True` + notificación, mover aquí `cuentas.views.aprobar_taller`), rechazar con motivo (nuevo campo o notificación), verificar, destacar, despublicar.
- Eliminación segura: bloquean citas (`SolicitudCita` CASCADE → historial), cupones con códigos (`CodigoCupon.cupon` es PROTECT), mantenimientos/hoja de vida registrados; ofrecer despublicar.

### Citas y servicios — aplica
- `talleres.SolicitudCita` (estados pendiente/confirmada/reprogramada/atendida/cancelada) y `garaje.ServicioTaller` / `RegistroServicio`.
- Listado con filtros por taller, estado y rango de fechas; solo lectura salvo cancelar por soporte (con motivo, va a la bitácora).

### Pagos y Plus — aplica
- `cuentas.Suscripcion` (solicitada/activa/cancelada, `inicia`, `vence`, `referencia_pago`). Hoy se activa desde `/admin/`.
- Acciones: activar (fija `inicia=reloj.hoy()`, `vence` = +30 días), renovar, cancelar; detalle en bitácora.
- No aplica: pasarela de pagos ni facturas (el pago es por Nequi/transferencia, fuera del sistema).

### Cupones — aplica
- `cupones.Cupon` y `CodigoCupon` (entregados, canjeados, por taller). Pausar/activar cupones, ver canjes, vencidos.

### Moderación — aplica
- `foro.Reporte` (`revisado`), `foro.Pregunta`/`Respuesta`, `talleres.Resena`.
- Marcar revisado, ocultar o borrar contenido (eliminación segura: respuestas hijas, votos), desactivar al autor desde la ficha de Usuarios.
- Pendiente de decidir: ¿ocultar en vez de borrar? Requiere un campo `oculto` (migración).

### Reportes — aplica parcialmente
- Rango de fechas y agregados por mes (cuentas, citas, canjes, Plus); rankings de talleres por citas atendidas y por calificación.
- Excel y PDF generados en el servidor: hoy no hay `openpyxl` ni librería de PDF en `requirements.txt`; agregar `openpyxl` (Excel) y, para PDF, `reportlab` o HTML→PDF. Decidir antes de instalar.

### Catálogos auxiliares — aplica
- `talleres.Barrio`, `Servicio`, `Marca`, `garaje.LineaMoto`, `garaje.TareaMantenimiento`. Hoy en `/admin/`.
- Eliminación segura: `Barrio`, `Marca`→`LineaMoto` y `LineaMoto`→`Moto` son PROTECT (el Collector ya lo detecta).
- No aplica: el despiece (`Despiece`, `Lamina`, `ParteDespiece`) se mantiene con `manage.py importar_despiece`, no a mano.

### Configuración — aplica (nuevo)
- No existe hoy. Modelo `Ajuste(clave, valor JSON)` + diccionario de valores por defecto en código (`consola/ajustes.py`); leer con `ajuste("plus_precio")`.
- Candidatos: precio y duración de Plus, contacto, textos de avisos, límites de cupos. Cada cambio con antes → después en la bitácora.

### Notificaciones y correos — aplica parcialmente
- `notificaciones.Notificacion` (leída/no leída) y `SuscripcionPush`: listado y conteos.
- Correos: hoy no se guarda registro de envíos ni su estado; haría falta un modelo `CorreoEnviado` (o un backend de correo que registre) — pendiente, sobre todo cuando se configure el SMTP.

### No aplica a TallerYa
- Reservas de viajes, destinos, itinerarios, tarifas por temporada y demás temática del proyecto de referencia.
- Pagos en línea con pasarela, reembolsos automáticos, facturación electrónica (no hay cobro en línea).
- Roles finos por permiso (editor, soporte…): hoy solo hay un rol administrador; si llega a hacer falta, ampliar `permisos.py` con permisos por sección en `Seccion`.
