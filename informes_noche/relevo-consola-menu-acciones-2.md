# Relevo: consola, menú «⋯», reportes y navegación sin recarga (sin commit)

## Hecho (pruebas rápidas: 925 OK)
1. Mecánicos (`domicilio/templates/domicilio/consola_mecanicos.html`, `domicilio/consola.py`): menú «⋯» con Pausar/Reactivar (valor de estado sigue siendo `suspendido`, sin migración; solo cambió el texto de la consola: «Pausado»), Verificar y «Ver reporte»; «Aprobar» chico a la vista si está por revisar. No quedan plantillas `consola_*.html` con botones viejos.
2. Usuarios (`consola/templates/consola/usuarios.html`, `consola/vistas/usuarios.py`, `consola.css`): píldoras compactas, domiciliario como sello redondo (verde/ámbar/gris con `title` y `aria-label`), columna Acciones con «⋯» (ver ficha, revisar verificación si está pendiente, cambiar rol y editar → ficha con ancla, activar/desactivar, eliminar con reglas). Íconos nuevos: ficha, lapiz, llave, encendido.
3. Reportes: sección `reportes` con `en_menu=False` (fuera de la barra lateral, sigue en `?seccion=reportes`); «Ver reporte» en Talleres y Mecánicos → `?seccion=reportes&taller=ID` / `&mecanico=ID` (`consola/vistas/reportes.py`, `reporte_detalle.html`, 12 meses). Mecánicos: no hay conteo de vistas ni clics (falta un modelo tipo `EventoDiario` para ellos); se muestran solicitudes de visita y reseñas nuevas, con nota en pantalla. Prueba nueva en `config/tests_piloto.py`; el mecánico no tiene prueba con datos.
4. Navegación sin recargar (`consola/static/consola/consola.js`): delegada en `#consola`; fetch de la página, reemplaza `.cs-principal`, nav (aria-current e insignias), select móvil, título, pushState/popstate, foco al h1, ancla `#`; si falla, recarga normal. Filtros y paginación pasan por ahí.

## Falta
- **Verificar en navegador** (no se pudo: el panel responde 403 y no acepta la cookie; usar `.claude/skills/revisar-ux/entrar.py` + Chrome sin ventana): clics en nav, atrás/adelante, filtros, paginación, menú «⋯» tras cambiar de sección, «Ver reporte» de un mecánico (usa `creado__date__gte`), sello y píldoras en 1280 y 375 px.
- Skill `revisar-ux` y captura final.
- Usuarios calcula `analizar_eliminacion` por fila (≈9 consultas × filas por página): medir con `optimizar-velocidad` si pesa.

## Ajustes posteriores (decisiones del usuario vía Ejecutivo; pruebas 206 OK, sin verificar en navegador)
- Pendientes: píldora «✓ Aprobar» (clase `cs-pildora-aprobar`) bajo «Por revisar» (mecánicos) y «Por aprobar» (talleres); la columna de acciones solo lleva «⋯» (Aprobar también dentro en mecánicos).
- «Verificado» en talleres y mecánicos: sello verde 16 px sin texto (`cs-sello-chico`) junto al estado.
- Usuarios: domiciliario = una píldora «Domiciliario» (ícono `moto_reparto` + sello verde / reloj ámbar / gris sin ícono) que reemplaza a «Motero» (`_rol_dom.html`); el sello redondo anterior ya no se usa. El ícono de moto es un dibujo propio: revisar a la vista.
