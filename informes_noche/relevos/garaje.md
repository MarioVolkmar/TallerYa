# Relevo — Garaje: vencimientos, hoja de vida y gastos

Única sesión que crea migraciones en `garaje` y dueña de `plan.py`. Sin commit.

## Hecho
- Historial único: cada Mantenimiento crea/enlaza su RegistroServicio (OneToOne `mantenimiento`, señales en `apps.py`); migración 0020 enlazó lo existente. Tarea del plan y precio desde la hoja de vida; Gastos sin doble conteo.
- Estados de verificación: pendiente / verificado / propio (`estado_verificacion`). Código QR ligado al registro (0021), componente único `static/garaje/js/codigo_taller.js` + endpoint `codigo_taller`.
- Gastos: detalle en modal y edición (`vista_gastos.py`, `gastos.html`).
- Niveles de color del plan (vencido, urgente ≤min(500 km, 10 %) o ≤7 días, pronto, ok) en agenda, Mi garaje, campana, 3D y despiece (`EstadoTarea.nivel/color`).
- Correcciones del auditor: migraciones 0023, 0026–0030 (rines, llantas, frenos, amortiguadores).
- Intervalos por línea: `garaje/intervalos.py` + `garaje/intervalos/*.json` (null = general, 0 = sin límite, versiones por año), `intervalo_para()` usado por la guía de Planos. Pruebas aisladas con `utiles_pruebas.usar_intervalos_generales`.

## Pendiente
- Correr la suite completa: van 0023–0030 e intervalos después de la última corrida completa (386 OK).
- Auditor Planos y Auditor mecánico siguen llenando `garaje/intervalos/*.json`. Regla: los rangos de versión deben cortar en un año que tenga despiece.
- La sesión "3D: fidelidad" está editando `moto.html` (secciones 02 y 03). Debe conservar `codigo_taller.js`, el cambio de precio según taller y `punto-{{ p.nivel|default:p.estado }}`.

## Archivos clave
`garaje/models.py`, `plan.py`, `hoja_vida.py`, `intervalos.py`, `gastos.py`, `vista_hoja_vida.py`, `vista_gastos.py`, `apps.py`, `forms.py`, `forms_hoja_vida.py`, `static/garaje/js/codigo_taller.js`, `templates/garaje/{hoja_vida,_hoja_vida_lista,_agenda,_tarea,gastos}.html`, pruebas `tests_hoja_vida`, `tests_gastos`, `tests_avisos`.
