# Plan del piloto TallerYa (aprobado 21-nov-2026)

Problema principal: oferta y demanda (talleres y moteros), no funciones. Rama `piloto`; respaldo: tag `respaldo-antes-piloto` en `main`. Producción (`C:\dev\TallerYa-produccion`, rama `produccion`): no tocar. Sin push sin permiso.

## Paso 0: respaldo
Commit de lo pendiente del 3D en `main` (modelos que usa el visor, glb.js, moto3d.js, Personalizar, herramientas_3d/, skill y fichas, package*.json, CLAUDE.md, .claude/settings.json, informes finales). Excluir: fotos de referencia «no publicar» (`xr190l-3d-nuevo/comparacion_*.jpg`), modelos sin uso (`xr190l_tripo2/3.glb`, `aerox155_tripo2.glb`), capturas intermedias, `privado/`. Suite rápida antes. Luego tag `respaldo-antes-piloto` y rama `piloto`.

## Paso 1: limpiar y medir
- Ocultar foro, suscripciones y referidos con un interruptor en la configuración (sin borrar código).
- Medición por taller: vistas del perfil y clics en WhatsApp/llamar; reporte mensual por taller en la consola.
- Botón de WhatsApp en el perfil con mensaje armado (moto, servicio, «te encontré en TallerYa»).

## Paso 2: kilometraje fácil (opus, medium)
- Perfil de uso da km/día inicial al registrar la moto.
- Con dos lecturas, promedio real; confirmación periódica de un toque («¿vas por unos 8.400 km?»).
- El taller registra km en cada servicio y recalibra.
- Cada recordatorio termina en «cotizar con un taller cercano» o «pedir mecánico a domicilio».
- Apoyado en `LecturaKm` y el plan de mantenimiento.

## Paso 3: facilitarle la vida al taller
- Dos caminos: (a) alta asistida (formulario rápido en la consola; fotos propias o del taller, nunca de Google; enlace sin cuenta para revisar, corregir y aprobar; autorización Ley 1581); (b) autoregistro desde el celular, pendiente de revisión.
- Precios de referencia SOLO de mano de obra («confirmado el dd/mm», recordatorio cada 2-3 meses). Opcionales: interruptor por taller «mostrar precios», apagado por defecto; si está apagado, el perfil muestra «Cotiza por WhatsApp». (Ajuste del usuario, 21-nov; tras hablar con talleres se decide si se quedan o solo hay cotización privada.)
- Servicio en 30 s: placa, km, qué se hizo, precio → hoja de vida del motero y reseña verificada.
- Reseñas abiertas con sello «verificada» si vienen de un servicio registrado.

## Paso 4: diagnóstico y chat
- Al terminar el diagnóstico (`garaje/vista_diagnostico.py`), botón «enviar a un taller o mecánico a domicilio».
- Fase 1: WhatsApp armado + enlace a ficha del diagnóstico (moto, km, síntomas, causa, fotos).
- Fase 2: chat propio, solo diseño; se construye si el piloto muestra uso.

## Pausado
3D (pendientes menores de la Aerox solo si el usuario lo pide).

## Reglas
Pruebas focalizadas por paso, `revisar-ux` en cambios visuales, suite rápida antes de cada commit en `piloto` (con permiso). Capturas al usuario con SendUserFile para aprobar cada paso. Una sesión a la vez si tocan los mismos archivos. Contexto del coordinador ≤150 mil; relevo en memoria.
