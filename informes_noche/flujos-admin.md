# Auditoría de flujos del administrador en la consola (23-nov)

**Método:** lectura de `consola/`, `domicilio/`, `domiciliarios/`, `proveedores/` y plantillas, más el render de cada sección con cuenta superadmin demo usando el cliente de pruebas de Django. No hubo cambios de código ni de datos.
**Límite:** el Browser pane negó el acceso a localhost, así que **no se revisó 375 px**. Los datos demo no traen pendientes (0 talleres, mecánicos, proveedores ni reportes), por lo que los pasos con pendientes salen del código y las plantillas.

## Flujos
| Flujo | Cómo llega | Pasos | Qué ve el solicitante | Riesgo |
|---|---|---|---|---|
| Mecánico a domicilio | Insignia en «Aprobaciones» y en la sección; **sin aviso al admin** | Aprobar (1 clic, sin confirmar) o Pausar (confirma) | Aprobado: notificación «ya está publicado». Pausado: notificación genérica «escríbenos si es un error». **Sin motivo ni «rechazar».** | Pausar un pendiente no explica nada |
| Taller (autoregistro) | Insignia (`activo=False`) | Aprobar (1 clic) / Pausar | Aprobado: notificación. **Pausar o rechazar: no se le avisa.** No hay «rechazar»: solo Pausar o Eliminar | Eliminar tiene resumen de dependencias y confirma |
| Domiciliario (Ruta) | Insignia en **Usuarios** (no en Aprobaciones); se aprueba desde la ficha | Aprobar / Rechazar con **motivo obligatorio** | Notificación con motivo; las fotos se borran al decidir | El mejor flujo; los otros deberían copiarlo |
| Proveedor | Insignia (`por_revisar`) | Aprobar (solo si ya aprobó su ficha) / Pausar | **Sin notificación de aprobación ni de pausa** (no usa `notificar`); no hay motivo | Aprobar con ficha pendiente da error claro |
| Moderación foro | Insignia en «Moderación» | Ocultar contenido (confirma) y **después** «Marcar revisado» | **El autor no se entera** de que ocultaron o borraron su contenido; el reportante tampoco | Ocultar no cierra el reporte: queda pendiente |
| Usuarios | Lista con filtros | Rol (confirma; admin pide casilla extra), activar/desactivar (confirma), editar, contraseña temporal (confirma, se ve una vez), eliminar (confirma y bloquea si hay motos, citas o cupones) | Cuenta desactivada: no se explica | Bien protegido: no se puede quitar el último admin ni editar a un superusuario |
| Métricas / Bitácora | Menú | Solo lectura; bitácora con filtros por acción, quién y fechas | n/a | Sin hallazgos |

## Hallazgos
**Importante**
1. **Sin «Rechazar con motivo» para mecánicos, talleres y proveedores.** Solo existe Pausar, y el aviso es genérico o no existe. El domiciliario ya lo hace bien (`domiciliarios/consola.py`). *Arreglo:* acción «Rechazar» con motivo obligatorio (mín. 4 caracteres), guardado y mostrado en el aviso, y el estado «Rechazado» visible en «Mi perfil».
2. **El taller y el proveedor no reciben aviso al ser aprobados, pausados o rechazados.** El taller solo lo recibe al publicarse (`_avisar_publicado`). El proveedor no recibe nada, ni siquiera al aprobarse (`proveedores/consola.py`). *Arreglo:* usar `notificar` en `proveedores.estado` y en `talleres.publicar` para pausas.
3. **El admin no se entera de nuevas solicitudes**, solo si abre la consola y mira la insignia. `tramites/views.py` ya notifica a los admins; los registros de mecánico, taller, proveedor y domiciliario no. *Arreglo:* `notificar` a los admins activos al registrarse alguien.
4. **Los domiciliarios pendientes cuentan en «Aprobaciones» pero viven en «Usuarios».** Esa sección tiene como insignia solo los domiciliarios, y el enlace de «Aprobaciones» va a la sección con más pendientes. *Arreglo:* pestaña «Domiciliarios» dentro de Aprobaciones, o una bandeja unificada «Por aprobar» con los cuatro tipos.
5. **El moderador no avisa al autor** cuando oculta o elimina su pregunta, respuesta o reseña, y eso es irreversible en el caso de eliminar. *Arreglo:* notificación al autor con el motivo («Contenido oculto por incumplir las normas») y registro del motivo en la bitácora.

**Detalle**
6. Aprobar un mecánico, un taller o un proveedor es un solo clic sin confirmar. Es publicar de cara al público; basta un `confirmar` que muestre el nombre.
7. «Pagos y Plus» cuenta en el total de pendientes pero no tiene vista (`vista=None`). Las solicitudes Plus solo se resuelven en el admin de Django. *Arreglo:* construir la sección o quitar la insignia.
8. Reportes del foro: «Ocultar contenido» no marca el reporte como revisado. *Arreglo:* que ocultar lo cierre, o añadir «Ocultar y cerrar».
9. Los reportes no se pueden reabrir ni listar los ya revisados (el filtro «Reportes» solo muestra los pendientes).
10. Un mecánico o un taller pausado y uno pendiente se parecen en la lista (la columna dice «Pausado» y el pendiente cae en la rama `else` de la plantilla). Distinguir «Rechazado» de «Pausado».
11. Falta revisar 375 px (tablas con el menú «⋯»); pendiente de una pasada con navegador.

**Bloqueantes:** ninguno. No se encontraron caminos sin salida ni acciones destructivas sin confirmación en usuarios, eliminaciones o contraseñas.

## Mejoras recomendadas
1. **Bandeja «Por aprobar»** única: mecánicos, talleres, proveedores y domiciliarios con insignia, antigüedad de la solicitud y botones Aprobar y Rechazar.
2. **Motivo de rechazo y plantillas de respuesta** («Falta tu cédula», «Foto borrosa») que lleguen por notificación y correo, siguiendo el patrón de Ruta.
3. **Aviso al admin** de cada nueva solicitud (notificación y, si se quiere, correo) para no depender de entrar a mirar.
4. **Avisos al autor** en moderación (oculto o eliminado, con motivo) y al reportante («lo revisamos»).
5. **Cerrar reportes al actuar** (ocultar o eliminar) y poder ver los ya revisados.

## Hecho (23-nov, sin commit)
- **1 y 10. Rechazar con motivo** (mín. 4 letras, diálogo común `data-motivo`): mecánicos, talleres y proveedores (`*.rechazar`). Estado «Rechazado» distinto de «Pausado» en listas y filtros; el solicitante lo ve en Mi perfil/panel (mecánico, taller). Al corregir y guardar su perfil, vuelve a «por revisar». Migraciones: `domicilio 0010`, `proveedores 0003`, `talleres 0028` (campo `motivo_rechazo`; estado «rechazado»).
- **2. Avisos** con `notificar`: mecánico (rechazo con motivo; aprobar y pausar ya existían) y taller (aprobar, pausar, rechazar). **Proveedor no tiene cuenta**, no hay a quién notificar: el motivo se ve en su enlace de ficha.
- **4. Bandeja «Por aprobar»** (`consola/vistas/aprobaciones.py`): 4 tipos, más antigua primero, pestañas, Aprobar/Rechazar. «Aprobaciones» y su insignia llevan ahí; el total ya no cuenta doble. Domiciliarios: «Revisar» + Rechazar (aprobar exige comparar placas en la ficha).
- **5. Moderación:** ocultar y eliminar piden motivo, avisan al autor y lo registran en la bitácora; ocultar cierra los reportes; filtro «Reportes: sin revisar / ya revisados / todos».
- **6.** Aprobar confirma con el nombre. **7.** «Pagos y Plus»: insignia quitada (sin vista).
- Pendiente: n.º 3 (otra sesión); reabrir reportes; plantillas de motivo por correo.
- Pruebas: `consola/tests_aprobaciones.py` + ajustes en tests de moderación y navegación. UX revisada a 1280 y 375 px sin desbordes.
- **Celular (375 px):** tablas de lista → tarjetas (≥44 px), sin scroll lateral en 13 pantallas medidas; selector «Estás en / Cambiar sección» con hoja de iconos y contadores; tema al pie; ficha de revisión (`?revisar=tipo-id`) con datos, «Falta», «Qué revisar» y Aprobar/Rechazar. Falta la pasada de diseño amplia (Usuarios, Moderación, filtros plegables, estados vacíos).
