# Sistema RPA - Automatización de Correos Electrónicos

## Descripción

El Sistema RPA es una herramienta de automatización que procesa correos electrónicos automáticamente. El sistema lee correos no leídos, extrae enlaces de los mensajes, y automatiza acciones web usando Selenium.

## Características Principales

- Lectura automática de correos electrónicos
- Extracción de enlaces de mensajes
- Automatización web con Selenium
- Base de datos para registro de actividades
- Limpieza automática de cache y datos antiguos
- Gestión mediante servicio systemd
- Logs detallados de todas las operaciones

## Estructura del Proyecto

```
rpa_system/
├── rpa/                    # Código principal del sistema
│   ├── main.py            # Archivo principal
│   ├── email_reader.py    # Lectura de correos
│   ├── driver_web.py      # Automatización web
│   ├── database.py        # Gestión de base de datos
│   └── notifier.py        # Notificaciones
├── config/                 # Configuración
│   └── env.example        # Variables de entorno
├── rpa_system.service     # Servicio systemd
├── gestionar_rpa.sh       # Gestor interactivo
├── rpa_runner.sh          # Script de ejecución manual
├── rpa_system.log         # Logs del sistema
├── rpa_database.db        # Base de datos SQLite
└── requirements.txt       # Dependencias Python
```

## Instalación

### Requisitos Previos

- Python 3.7 o superior
- Sistema operativo Linux
- Acceso a correo electrónico IMAP
- Permisos de administrador

### Pasos de Instalación

1. **Clonar o descargar el proyecto:**
   ```bash
   cd /root
   git clone [URL_DEL_REPOSITORIO] rpa_system
   cd rpa_system
   ```

2. **Instalar dependencias:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configurar variables de entorno:**
   ```bash
   cp config/env.example .env
   nano .env
   ```
   
   Configurar las siguientes variables:
   - `EMAIL`: Tu dirección de correo
   - `PASSWORD`: Tu contraseña de correo
   - `IMAP_SERVER`: Servidor IMAP (ej: imap.gmail.com)
   - `SENDER_FILTER`: Remitente específico a procesar
   - `BUTTON_SELECTOR`: Selector CSS del botón a hacer clic
   - `TIMEOUT_SECONDS`: Tiempo de espera para elementos web

4. **Configurar el servicio systemd:**
   ```bash
   sudo cp rpa_system.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable rpa_system
   ```

5. **Iniciar el servicio:**
   ```bash
   sudo systemctl start rpa_system
   ```

## Gestión del Sistema

### Usando el Gestor Interactivo

El sistema incluye un gestor interactivo que facilita la administración:

```bash
./gestionar_rpa.sh
```

**Opciones disponibles:**
- Ver estado del sistema
- Ver logs recientes
- Ver logs en tiempo real
- Detener sistema
- Iniciar sistema
- Reiniciar sistema
- Ver archivo de log

### Comandos Directos

**Verificar estado:**
```bash
sudo systemctl status rpa_system
```

**Iniciar sistema:**
```bash
sudo systemctl start rpa_system
```

**Detener sistema:**
```bash
sudo systemctl stop rpa_system
```

**Reiniciar sistema:**
```bash
sudo systemctl restart rpa_system
```

**Ver logs del servicio:**
```bash
sudo journalctl -u rpa_system -f
```

**Ver logs del archivo:**
```bash
tail -f rpa_system.log
```

### Ejecución Manual

Para pruebas o ejecución manual:

```bash
python3 rpa/main.py
```

## Configuración

### Variables de Entorno

Crear archivo `.env` con las siguientes variables:

```
EMAIL=tu_correo@gmail.com
PASSWORD=tu_contraseña
IMAP_SERVER=imap.gmail.com
SENDER_FILTER=remitente_especifico@dominio.com
BUTTON_SELECTOR=button[type="submit"]
TIMEOUT_SECONDS=10
```

### Configuración de Correo

Para Gmail, es necesario:
1. Habilitar autenticación de dos factores
2. Generar contraseña de aplicación
3. Usar la contraseña de aplicación en lugar de la contraseña normal

## Configuración de Eliminación Automática

El sistema incluye la funcionalidad de eliminación automática de correos después de procesarlos exitosamente:

```bash
# Habilitar eliminación automática
AUTO_DELETE_EMAILS=true

# Deshabilitar eliminación automática
AUTO_DELETE_EMAILS=false
```

**Comportamiento:**
- **Correos procesados exitosamente**: Se eliminan automáticamente si está habilitado
- **Correos con errores**: Se mantienen en la bandeja para revisión manual
- **Solo se eliminan correos después de completar el proceso** (hacer clic en botón específico)

## Monitoreo y Logs

### Archivos de Log

- **rpa_system.log**: Log principal del sistema
- **journalctl**: Logs del servicio systemd

### Información en los Logs

- Inicio y fin de ciclos de procesamiento
- Correos procesados y resultados
- Errores y excepciones
- Limpieza automática de cache
- Estado de la base de datos

### Comandos de Monitoreo

```bash
# Ver logs recientes
tail -20 rpa_system.log

# Ver logs en tiempo real
tail -f rpa_system.log

# Buscar errores
grep "ERROR" rpa_system.log

# Ver logs del servicio
sudo journalctl -u rpa_system -n 50
```

## Base de Datos

El sistema utiliza SQLite para almacenar:
- Registros de correos procesados
- Enlaces extraídos
- Estados de procesamiento
- Errores y observaciones

### Limpieza Automática

El sistema limpia automáticamente:
- Registros antiguos (más de 30 días)
- Cache de Selenium (cada 7 días)
- Logs antiguos

## Solución de Problemas

### Problemas Comunes

1. **Error de autenticación de correo:**
   - Verificar credenciales en .env
   - Habilitar autenticación de dos factores
   - Usar contraseña de aplicación

2. **Error de Selenium:**
   - El sistema limpia automáticamente el cache
   - Verificar conexión a internet
   - Revisar logs para detalles específicos

3. **Servicio no inicia:**
   ```bash
   sudo systemctl status rpa_system
   sudo journalctl -u rpa_system -n 20
   ```

4. **Espacio en disco:**
   - El sistema limpia automáticamente cache y logs
   - Verificar con: `du -sh ~/.cache/selenium/`

### Verificación de Funcionamiento

```bash
# Verificar que el servicio está activo
sudo systemctl is-active rpa_system

# Verificar logs recientes
tail -10 rpa_system.log

# Verificar procesos
ps aux | grep python | grep main.py
```

## Mantenimiento

### Limpieza Manual

Si es necesario limpiar manualmente:

```bash
# Limpiar cache de Selenium
rm -rf ~/.cache/selenium/chrome/linux64/*
rm -rf ~/.cache/selenium/chromedriver/linux64/*

# Limpiar logs antiguos
tail -n 1000 rpa_system.log > rpa_system.log.tmp
mv rpa_system.log.tmp rpa_system.log
```

### Actualización

Para actualizar el sistema:

1. Detener el servicio
2. Hacer backup de la base de datos
3. Actualizar archivos
4. Reiniciar el servicio

```bash
sudo systemctl stop rpa_system
cp rpa_database.db rpa_database.db.backup
# Actualizar archivos
sudo systemctl start rpa_system
```

## Seguridad

- El sistema ejecuta con permisos de root
- Las credenciales se almacenan en archivo .env
- Los logs pueden contener información sensible
- Se recomienda configurar firewall apropiado

## Soporte

Para problemas o preguntas:
1. Revisar logs del sistema
2. Verificar configuración en .env
3. Comprobar estado del servicio
4. Revisar documentación de dependencias

## Dependencias

- Python 3.7+
- selenium
- imap-tools
- python-dotenv
- openpyxl
- sqlite3 (incluido con Python) # automatizacion
