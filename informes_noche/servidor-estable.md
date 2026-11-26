# tallerya.co estable (25-nov-2026)

## Estado
**Instalado y funcionando (25-nov, 21:06).** Las 3 tareas están creadas, web y túnel corren en segundo plano (no dependen de ninguna terminal), `/`, `/talleres/` y `/cuenta/entrar/` responden 200 y quedó el primer respaldo completo (`2026-11-25_210627_completo`, 659 archivos). Accesos Apagar/Encender en el escritorio. Registro: `C:\dev\servidor-tallerya\logs\instalar.log`.

Antes: waitress lanzado desde una consola; cloudflared suelto (no es servicio de Windows ni tarea). Si se cerraban o se reiniciaba el PC, el sitio caía.

## Qué instala (scripts en `C:\dev\servidor-tallerya\`, fuera del repo)
| Tarea programada | Qué hace |
|---|---|
| `TallerYa web` | `vigilar.ps1 -Servicio web`: arranca waitress, lo reinicia si se cierra o si pasa 3 min sin responder |
| `TallerYa tunel` | `vigilar.ps1 -Servicio tunel`: cloudflared con `~\.cloudflared\config.yml`, lo reinicia si se cierra |
| `TallerYa respaldo` | diario 3:00 a. m. (o al prender, si estaba apagado) en `C:\dev\respaldos\auto\` |

Las dos primeras arrancan al prender el PC (sin iniciar sesión) y se revisan cada 5 min. Corren como `volkm` (S4U, sin guardar contraseña, sin privilegios). Producción toma su configuración de `.env`.

## Respaldos
| Carpeta | Cuándo | Contiene |
|---|---|---|
| `..._completo` | el primero y luego cada 7 días | base, `media/`, `privado/`, `.env` |
| `..._diario` | los demás días | base completa (usuarios, talleres y todos los datos) y solo los archivos nuevos o cambiados desde el último completo |

Se borran los de más de 14 días, nunca el último completo ni uno del que dependa un diario.

`privado/` guarda documentos de usuarios (SOAT, técnico-mecánica, tarjeta de propiedad, pólizas, fotos de verificación de identidad) y el script de arranque antiguo. Las fotos de identidad que el sitio borra al decidir pueden seguir en respaldos viejos unas semanas.

**Cambio de servidor:** armar el último respaldo (ver «Restaurar») y copiar además `~\.cloudflared\`, que no entra en el respaldo; el código sale del repositorio. El respaldo lleva `.env` con las claves: no compartirlo. Los respaldos quedan en el mismo disco: copiar de vez en cuando a una memoria USB. El respaldo manual `produccion-2026-11-23` no se toca.

## Reinstalar (PowerShell como administrador; ya está hecho)
```powershell
powershell -ExecutionPolicy Bypass -File C:\dev\servidor-tallerya\instalar.ps1
```
Corte esperado: segundos en la web, ninguno en el túnel. Debe terminar con `200` en `/`, `/talleres/` y `/cuenta/entrar/`. Después, **no volver a usar `privado\reiniciar.ps1`** y cerrar la pestaña vieja.

## Apagar y encender
Doble clic en **Apagar TallerYa** o **Encender TallerYa** (en el escritorio tras instalar) y aceptar el permiso de administrador. Apagado sigue apagado aunque se reinicie el PC, hasta usar Encender. El respaldo diario sigue corriendo. Si apagas a propósito, pausa el monitor.

## Reiniciar (PowerShell como administrador)
```powershell
powershell -ExecutionPolicy Bypass -File C:\dev\servidor-tallerya\reiniciar.ps1
```
Con `-Tunel` al final reinicia también cloudflared. Usarlo tras actualizar el código de producción. Registros: `C:\dev\servidor-tallerya\logs\`; respaldos: `C:\dev\respaldos\auto\respaldos.log`.

## Restaurar un respaldo (PowerShell como administrador)
1. Armar la carpeta (junta el completo con el diario elegido; cambiar el nombre):
```powershell
C:\dev\TallerYa-produccion\venv\Scripts\python.exe C:\dev\servidor-tallerya\respaldar.py --armar 2026-11-27_030000_diario C:\dev\respaldos\armado
```
2. Reemplazar la base y `media/` (lo actual se guarda aparte):
```powershell
$r = 'C:\dev\respaldos\armado'; $p = 'C:\dev\TallerYa-produccion'
Disable-ScheduledTask 'TallerYa web'; Stop-ScheduledTask 'TallerYa web'
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object CommandLine -match 'servir_produccion' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
$antes = "C:\dev\respaldos\antes-de-restaurar-$(Get-Date -Format yyyyMMdd-HHmmss)"; New-Item -ItemType Directory $antes
Move-Item "$p\db.sqlite3*", "$p\media" $antes
Copy-Item "$r\db.sqlite3" $p; Copy-Item "$r\media" "$p\media" -Recurse
Enable-ScheduledTask 'TallerYa web'; Start-ScheduledTask 'TallerYa web'
```
Documentos privados, solo si se perdieron: `Copy-Item "$r\privado\*" "$p\privado" -Recurse -Force`. En un servidor nuevo, copiar también `.env`. Un archivo borrado entre el completo y el diario puede reaparecer.

## Deshacer la instalación
```powershell
Get-ScheduledTask 'TallerYa*' | ForEach-Object { Stop-ScheduledTask $_.TaskName; Unregister-ScheduledTask $_.TaskName -Confirm:$false }
```
Luego volver a lanzar a mano `privado\reiniciar.ps1` y `cloudflared tunnel run tallerya`.

## Monitor de caídas (UptimeRobot, plan gratis) — lo hace el usuario
1. Entrar a https://uptimerobot.com y elegir **Register for FREE**; usar tu correo y una contraseña propia; confirmar el correo.
2. **+ New monitor** → tipo **HTTP(s)**.
3. URL: `https://tallerya.co/cuenta/entrar/` · nombre: `TallerYa` · intervalo: 5 minutos.
4. En avisos, marcar tu correo. Opcional: instalar la app en el celular y activar las notificaciones.
5. **Create monitor**. En 5 min debe salir en verde (*Up*).

El plan gratis puede estar limitado a uso no comercial: revisar sus condiciones; si no sirve, alternativas con plan gratis: Better Stack o HetrixTools.

## Pendiente de comprobar tras instalar
- Reiniciar el PC una vez, **sin iniciar sesión**, y abrir tallerya.co desde el celular.
- Probar Apagar y Encender.
- La suspensión ya está en «nunca». Windows Update puede reiniciar el PC; las tareas lo levantan solas.
