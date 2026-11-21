# Relevo: Yamaha FZ25 3D desde Tripo de una sola malla (ronda 1 hecha, ver informe.md)


**21-nov:** ronda 1 entregada (GLB en `?v=1`, ficha `fichas/fz25.py`). Pendientes y comandos en `informe.md`.
Esta sesión (Eco Deluxe) llegó a su tope de contexto antes de arrancar. **Nada hecho todavía para la FZ25.**

## Encargo (del coordinador «Ejecutivo»)
- Modelo: `C:\Users\volkm\Downloads\modelo-3d-fz25.glb` (UNA malla, sin despiece). Copiarlo a `privado/tripo/fz25/`.
- Fotos: `FOTOS_MODELADO_TRIPO/yamaha_fz_25/`.
- Despiece propio con Blender (islas, bisect, normales, bordes limpios). Meta: el nivel de la Eco Deluxe, sobre todo en
  las luces. Llantas integradas con el rin y a su medida, sin nada flotando y sin piezas genéricas del visor encima.
- Scripts en `herramientas_3d/fz25/`. GLB en `garaje/static/garaje/modelos/fz25_tripo.glb`, conectado en `MODELOS_TRIPO`
  de `moto3d/glb.js` (clave tipo `"fz[ _-]*25"`, con `?v=1`; cambio mínimo).
- Si `usuario@prueba.com` no tiene una FZ25, crearla en los datos de prueba.
- Capturas `final_lateral.png`, `final_tres_cuartos.png` y `final_luces.png` y un informe corto en esta carpeta.
- Límite 1 h, sin commit. Un solo Blender a la vez y validar con `npx gltf-transform validate`.

## Leer primero
- `informes_noche/ecodeluxe-3d/metodo.md`: el método completo, con luces, materiales, extras y trampas.
- Herramientas reutilizables: `herramientas_3d/ecodeluxe100/blender/glbio.py` (leer y escribir el formato del visor) y
  `arreglos_v5.py` (`cortar()` por plano; faro con mica, aro, reflector y bombillo; rin escalado a su medida).
- La skill `moto-3d-tripo` ya está hecha para **una malla fundida** (motor + ficha por moto). Seguramente conviene usarla
  para el despiece y después aplicar las luces y el rin del método de la Eco.

## Ojo
- En la sesión de la Eco el acceso a `privado/` estaba **denegado** por permisos (ni leer ni copiar). Si la sesión nueva
  tampoco puede, pedirle al usuario que copie el GLB o que dé permiso. No hay que saltarse la restricción.
- Panel del navegador oculto: usar `/garaje/<pk>/vista-3d/`, esperar ~1,5 s y llamar a `__visor.cuadro()` antes de capturar.
- Modelo y esfuerzo sugeridos: `opus` con esfuerzo `medium` (3D).
