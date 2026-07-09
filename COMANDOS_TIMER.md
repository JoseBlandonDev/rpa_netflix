# Sistema RPA - Comandos y Funcionalidades

## Ejecución por Timer

El sistema corre en modo de **ciclo único**: cada invocación de `rpa/main.py` procesa lo que encuentra y termina, no queda corriendo en background. La ejecución periódica la da `rpa_system.timer` (systemd), que dispara `rpa_system.service` (tipo `oneshot`) **cada 30 segundos** (`OnCalendar=*:*:00/30`).

```bash
# Ver próximas ejecuciones programadas
sudo systemctl list-timers rpa_system.timer

# Ver estado del timer
sudo systemctl status rpa_system.timer

# Iniciar / detener / reiniciar el timer
sudo systemctl start rpa_system.timer
sudo systemctl stop rpa_system.timer
sudo systemctl restart rpa_system.timer

# Disparar una ejecución manual (un solo ciclo)
sudo systemctl start rpa_system.service
```

## Filtro de Correos por Tiempo

`get_unread_emails()` solo devuelve correos no leídos del remitente configurado en `SENDER_FILTER` **recibidos en los últimos 5 minutos**. Esto evita reprocesar correos viejos si el timer estuvo detenido y evita que un correo se quede "atascado" si por algún motivo no se pudo marcar como leído. El valor de 5 minutos está fijo en el código (`rpa/email_reader.py`, `get_unread_emails`), no es configurable por `.env`.

## Timeout de Conexiones IMAP

Todas las operaciones IMAP (leer, marcar como leído, eliminar) usan un timeout de socket configurable:

```bash
# En .env
IMAP_TIMEOUT=30   # segundos (valor por defecto si no se define)
```

Si una operación excede el timeout, se registra un error y el ciclo continúa (no se cuelga el proceso). Buscar en logs:

```bash
grep "Timeout" rpa_system.log
```

## Funcionalidad de Eliminación Automática de Correos

### Descripción
El sistema puede eliminar automáticamente un correo de la bandeja después de procesarlo, sin importar el resultado (éxito, fallo, sin URL o error).

### Configuración

```bash
# Habilitar eliminación automática
AUTO_DELETE_EMAILS=true

# Deshabilitar eliminación automática
AUTO_DELETE_EMAILS=false
```

**Valores válidos para habilitar:** `true`, `1`, `yes`, `on`
**Valores válidos para deshabilitar:** `false`, `0`, `no`, `off` (o la variable ausente)

### Comportamiento del Sistema

Se evalúa `AUTO_DELETE_EMAILS` después de cada uno de estos desenlaces, en `rpa/main.py`:

| Desenlace | Registro en BD | ¿Se elimina si está habilitado? |
|---|---|---|
| Clic exitoso en el botón | `SUCCESS` | Sí |
| Clic fallido en el botón | `FAILED` | No se intenta eliminar en el flujo actual |
| Sin URL válida encontrada | `NO_URL` | Sí |
| Excepción durante el procesamiento | `ERROR` | Sí |
| Solicitud de reporte procesada exitosamente | (no aplica, es reporte) | Sí |

Si `AUTO_DELETE_EMAILS` está deshabilitado, el correo queda marcado como leído pero se mantiene en la bandeja para revisión manual.

### Logs del Sistema

Mensajes reales que emite el sistema (`rpa/main.py`, `rpa/email_reader.py`):

```
INFO - Correo eliminado
INFO - Correo mantenido (eliminación deshabilitada)
INFO - Correo sin URL eliminado
INFO - Correo sin URL mantenido (eliminación deshabilitada)
INFO - Correo con error eliminado
INFO - Correo con error mantenido (eliminación deshabilitada)
INFO - Correo de reporte eliminado
WARNING - Error al eliminar correo
WARNING - Error al eliminar correo sin URL
WARNING - Error al eliminar correo con error
WARNING - Error al eliminar correo de reporte
```

### Comandos de Gestión

```bash
# Ver logs relacionados con eliminación de correos
grep -i "eliminad" rpa_system.log

# Contar correos eliminados exitosamente
grep -c "eliminado$" rpa_system.log

# Ver advertencias de eliminación fallida
grep "Error al eliminar" rpa_system.log
```

### Cambiar Configuración en Tiempo Real

```bash
nano .env
# Cambiar AUTO_DELETE_EMAILS=true/false

# No hace falta reiniciar ningún proceso: cada ejecución del timer
# vuelve a cargar el .env desde cero (no hay proceso persistente).
```

### Consideraciones de Seguridad

- **Los correos eliminados no se pueden recuperar** desde la bandeja
- Los registros en la base de datos se conservan siempre, independientemente de la eliminación del correo
- Se puede deshabilitar en cualquier momento editando `.env`, sin reiniciar servicios

### Solución de Problemas

**Correos que no se eliminan:**
1. Confirmar `AUTO_DELETE_EMAILS=true` en `.env`
2. Revisar logs: `grep "Error al eliminar" rpa_system.log`
3. Confirmar que la cuenta IMAP tiene permisos para eliminar mensajes
4. Confirmar que no se superó `IMAP_TIMEOUT` durante la eliminación

**No aparecen logs de eliminación:**
1. Verificar que `rpa_system.log` se está generando: `ls -la rpa_system.log`
2. Verificar que el timer se está ejecutando: `sudo systemctl list-timers rpa_system.timer`
3. Confirmar que efectivamente llegaron correos de `SENDER_FILTER` en los últimos 5 minutos

### Integración con Otros Sistemas

- **Base de datos**: los correos eliminados siguen registrados; la eliminación solo afecta la bandeja de entrada, no el historial
- **Reportes**: cualquier correo (de cualquier remitente) con "REPORTE" en asunto o cuerpo dispara el envío de un Excel con el historial completo (ver `rpa/notifier.py` y `Database.export_to_excel`)
