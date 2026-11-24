# Usabilidad en celular (375 y 360 px), sin la consola

Método: Chrome sin ventana (el panel integrado rechazó localhost) con CDP, emulación móvil, sesiones demo de motero,
taller (paisa) y mecánico; script propio: scroll lateral, desbordes, toques < 44 px, texto cortado, tablas anchas.
Servidor: el de otra sesión en 8001 (mismo código).

| Página / rol | Antes | Arreglo |
|---|---|---|
| Portada, directorio, ficha de taller, mecánicos | chips «rápidos» 40 px, «Ver todos» 40, favorito y WhatsApp 40 | `min-height`/tamaño 44 en móvil |
| Emergencias, diagnóstico, despiece, cupones | botón «Obtener cupón» 41, enlace de taller 19 | 44 px; zona de toque ampliada |
| SOAT / tecnomecánica | campo 42, «Ver precio» 43, enlaces de datos 18 | 44 px; `::after` en enlaces |
| Registro y entrar | pestañas motero/aliado 38, ojo de clave 32, «Olvidaste» 23 | 44 px; zona ampliada |
| Garaje, moto, hoja de vida, editar | «Volver», accesos y «Editar» 40, filtros 40, «Agregar fecha» 30 | 44 px |
| Panel de taller | botones de cita desbordaban a 423 px (recortados) | `flex-wrap` en `.pt-cita-botones/form` (talleres.css) |
| Citas, servicios, agenda, precios, estadísticas, perfil, reseñas, descuentos | filtros 34, WhatsApp 34, «Historial» 31, estrellas 27 | 44 px |
| Panel, solicitudes, precios, perfil, descuentos del mecánico | «Editar/Pausar» 31, filtros 40, enlaces 19-31 | 44 px |
| Registro de mecánico (horario) | días 34, horas 42, «Agregar» 19 | 44 px; `.hz-dias` envuelve (si no, desbordaba a 360) |
| Mi cuenta (motero, taller, mecánico) | acciones de seguridad 40, «Reenviar» 34, «Confirmar» 25 | 44 px |
| Visor 3D (botones) | 36-40 | 44 px |
| Barra inferior | todas: contenido termina a 60 px del borde (padding 60 ≥ barra 61) | sin cambio, correcto |

CSS: bloque «Móvil: toques de 44 px» al final de `tallerya.css` (clases compartidas por varias secciones; `selects-estilo`
estaba en espera) y `flex-wrap` en `secciones/talleres.css`. Sin Tailwind nuevo.

Resultado: ninguna página con scroll lateral a 375 ni 360. Pendientes y notas:
- Foro, Plus y diagrama responden 404 (piloto oculta lo social con `PILOTO_OCULTAR_SOCIAL`): no auditados.
- Burbuja «¿Te ayudo?» de Chispa (89x31) y logo del encabezado (100x40): decorativos/aceptados; subir a 44 pide tocar `ayuda/…chispa-chat.css`.
- Falsos positivos: etiquetas `sr-only`, estrellas, iframe del mapa (recortado), enlaces con zona ampliada por `::after`.
- Sin commit.
