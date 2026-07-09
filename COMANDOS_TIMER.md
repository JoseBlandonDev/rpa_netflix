# Sistema RPA - Comandos y Funcionalidades

## Funcionalidad de Eliminación Automática de Correos

### Descripción
El sistema RPA ahora incluye la funcionalidad de **eliminación automática de correos** después de procesarlos exitosamente. Esta característica ayuda a optimizar el espacio en la bandeja de entrada y mantener la organización del correo.

### Configuración

#### Variable de Entorno
Para habilitar o deshabilitar la eliminación automática, configurar en el archivo `.env`:

```bash
# Habilitar eliminación automática
AUTO_DELETE_EMAILS=true

# Deshabilitar eliminación automática
AUTO_DELETE_EMAILS=false
```

**Valores válidos para habilitar:**
- `true`, `1`, `yes`, `on`

**Valores válidos para deshabilitar:**
- `false`, `0`, `no`, `off`

### Comportamiento del Sistema

#### 1. Procesamiento de URLs
- **Correo procesado exitosamente**: Se elimina automáticamente si `AUTO_DELETE_EMAILS=true`
- **Correo con error**: Se mantiene en la bandeja para revisión manual
- **Correo sin link válido**: Se mantiene en la bandeja

#### 2. Solicitudes de Reporte
- **Reporte enviado exitosamente**: Se elimina automáticamente si `AUTO_DELETE_EMAILS=true`
- **Error en generación de reporte**: Se mantiene en la bandeja para revisión manual

### Logs del Sistema

#### Mensajes de Eliminación Exitosa
```
INFO - Correo eliminado exitosamente: [Asunto del correo] (UID: [UID])
INFO - Correo eliminado automáticamente después de procesamiento exitoso: [Asunto del correo]
INFO - Correo de reporte eliminado automáticamente después de envío exitoso: [Asunto del correo]
```

#### Mensajes de Eliminación Fallida
```
WARNING - No se pudo eliminar el correo después del procesamiento: [Asunto del correo]
WARNING - No se pudo eliminar el correo de reporte después del envío: [Asunto del correo]
```

#### Mensajes de Funcionalidad Deshabilitada
```
INFO - Eliminación automática deshabilitada, correo mantenido: [Asunto del correo]
INFO - Eliminación automática deshabilitada, correo de reporte mantenido: [Asunto del correo]
```

### Comandos de Gestión

#### Ver Estado de Eliminación Automática
```bash
# Ver logs relacionados con eliminación
grep "eliminado\|eliminación" rpa_system.log

# Ver logs de eliminación exitosa
grep "eliminado exitosamente" rpa_system.log

# Ver logs de eliminación fallida
grep "No se pudo eliminar" rpa_system.log
```

#### Cambiar Configuración en Tiempo Real
```bash
# Editar archivo de configuración
nano .env

# Cambiar AUTO_DELETE_EMAILS=true a AUTO_DELETE_EMAILS=false
# o viceversa

# Reiniciar el servicio para aplicar cambios
sudo systemctl restart rpa_system
```

### Consideraciones de Seguridad

#### Ventajas
- **Optimización de espacio**: Reduce el uso de almacenamiento en la bandeja
- **Organización**: Mantiene la bandeja limpia de correos procesados
- **Automatización**: No requiere intervención manual para limpieza

#### Precauciones
- **Pérdida de datos**: Los correos eliminados no se pueden recuperar
- **Auditoría**: Solo se eliminan correos procesados exitosamente
- **Configuración**: Se puede deshabilitar fácilmente si es necesario

### Solución de Problemas

#### Correos que no se eliminan
1. **Verificar configuración**: Confirmar que `AUTO_DELETE_EMAILS=true` en `.env`
2. **Revisar logs**: Buscar mensajes de error en la eliminación
3. **Verificar permisos**: El sistema debe tener permisos de escritura en la bandeja
4. **Reiniciar servicio**: Aplicar cambios de configuración

#### Logs de eliminación faltantes
1. **Verificar nivel de logging**: Asegurar que esté configurado en INFO o superior
2. **Revisar archivo de log**: Confirmar que `rpa_system.log` se esté generando
3. **Verificar permisos**: El sistema debe poder escribir en el archivo de log

### Monitoreo y Mantenimiento

#### Verificación Diaria
```bash
# Ver logs de eliminación del día
grep "$(date +%Y-%m-%d)" rpa_system.log | grep "eliminado"

# Contar correos eliminados exitosamente
grep "eliminado exitosamente" rpa_system.log | wc -l

# Verificar errores de eliminación
grep "No se pudo eliminar" rpa_system.log | wc -l
```

#### Limpieza de Logs
```bash
# Mantener solo los últimos 1000 logs de eliminación
tail -n 1000 rpa_system.log | grep "eliminado" > eliminacion_logs.tmp
mv eliminacion_logs.tmp eliminacion_logs.txt
```

### Integración con Otros Sistemas

#### Base de Datos
- Los correos eliminados siguen registrados en la base de datos
- Se mantiene el historial completo de procesamiento
- La eliminación solo afecta la bandeja de entrada, no los registros

#### Sistema de Notificaciones
- Las notificaciones de eliminación se registran en los logs
- No se envían notificaciones externas sobre eliminación
- El sistema mantiene trazabilidad completa de todas las operaciones 