# Sistema RPA - Automatización de Correos Electrónicos (Netflix)

## Descripción

El Sistema RPA es una herramienta de automatización que procesa correos electrónicos de Netflix automáticamente. El sistema lee los correos no leídos recibidos en los últimos 5 minutos, extrae el enlace de actualización de ubicación, y hace clic en el botón correspondiente usando Selenium. También puede responder a solicitudes de reporte por correo con un archivo Excel del historial de procesamiento.

El sistema **no corre como un proceso continuo**: se ejecuta en modo de **ciclo único** (procesa lo que encuentra y termina) y es disparado periódicamente por un **timer de systemd**.

## Características Principales

- Lectura de correos no leídos de los últimos 5 minutos, filtrados por remitente
- Extracción de enlaces mediante un patrón configurable (`LINK_PATTERN`)
- Automatización web con Selenium (modo headless)
- Timeout configurable en las conexiones IMAP para evitar cuelgues
- Eliminación automática opcional de correos ya procesados
- Registro de correos sin URL válida como fallidos (`NO_URL`) en vez de ignorarlos
- Respuesta automática a solicitudes de reporte ("REPORTE" en asunto/cuerpo) con un Excel adjunto
- Base de datos SQLite para registro de actividades (éxitos, fallos, errores)
- Limpieza automática de registros antiguos y de cache de Selenium
- Ejecución periódica mediante `rpa_system.timer` (systemd)
- Logs detallados de todas las operaciones

## Estructura del Proyecto

```
automatizacion/
├── rpa/                     # Código principal del sistema
│   ├── main.py             # Orquesta el ciclo de ejecución
│   ├── email_reader.py     # Lectura IMAP, filtrado y extracción de links
│   ├── driver_web.py       # Automatización web con Selenium
│   ├── database.py         # Gestión de base de datos SQLite y export a Excel
│   └── notifier.py         # Envío de reportes por correo (SMTP)
├── config/
│   └── env.example         # Plantilla de variables de entorno
├── rpa_system.service      # Servicio systemd (oneshot)
├── rpa_system.timer        # Timer systemd que dispara el servicio
├── gestionar_rpa_timer.sh  # Gestor interactivo (timer, uso actual)
├── gestionar_rpa.sh        # Gestor interactivo legado (servicio continuo)
├── rpa_runner.sh           # Script alternativo de ejecución manual con lockfile
├── rpa_system.log          # Logs del sistema
├── rpa_database.db         # Base de datos SQLite
├── reporte_rpa.xlsx        # Último reporte Excel generado
└── requirements.txt        # Dependencias Python
```

## Instalación

### Requisitos Previos

- Python 3.7 o superior
- Sistema operativo Linux con systemd
- Google Chrome / Chromium (para Selenium)
- Acceso a correo electrónico IMAP (y SMTP si se usa la función de reportes)
- Permisos de administrador (systemd corre el servicio como root)

### Pasos de Instalación

1. **Clonar el proyecto:**
   ```bash
   cd /root
   git clone https://github.com/JoseBlandonDev/rpa_netflix.git automatizacion
   cd automatizacion
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

4. **Instalar el servicio y el timer:**
   ```bash
   sudo cp rpa_system.service /etc/systemd/system/
   sudo cp rpa_system.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now rpa_system.timer
   ```

   El servicio (`rpa_system.service`) es de tipo `oneshot`: no se habilita ni se inicia directamente, es el `timer` el que lo dispara.

## Configuración

### Variables de Entorno

Ver `config/env.example` para la plantilla completa. Variables disponibles:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `IMAP_SERVER` | Servidor IMAP de lectura de correo | `imap.gmail.com` |
| `IMAP_PORT` | Puerto IMAP | `993` |
| `IMAP_TIMEOUT` | Timeout en segundos para las conexiones IMAP | `30` |
| `EMAIL_ADDRESS` | Cuenta de correo que se lee vía IMAP | — (requerido) |
| `EMAIL_PASSWORD` | Contraseña de aplicación de esa cuenta | — (requerido) |
| `SENDER_FILTER` | Remitente exacto a procesar | `netflix.com` |
| `LINK_PATTERN` | Fragmento de URL que identifica el link a hacer clic | `https://www.netflix.com/account/update-primary-location` |
| `BUTTON_SELECTOR` | Selector CSS del botón a hacer clic en la página | `button[type="submit"]` |
| `TIMEOUT_SECONDS` | Timeout de Selenium (carga de página / espera del botón) | `10` |
| `DB_PATH` | Ruta del archivo SQLite | `rpa_database.db` |
| `AUTO_DELETE_EMAILS` | Elimina automáticamente los correos ya procesados | `false` |

**Para la funcionalidad de reportes por correo** (ver sección más abajo) también se necesitan, aunque no están en `env.example` todavía:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `EMAIL_HOST` | Servidor SMTP para enviar el reporte | `smtp.gmail.com` |
| `EMAIL_PORT` | Puerto SMTP | `587` |
| `EMAIL_USER` | Cuenta remitente del reporte | — (requerido) |
| `EMAIL_PASS` | Contraseña de aplicación de esa cuenta | — (requerido) |

### Configuración de Correo (Gmail)

1. Habilitar autenticación de dos factores
2. Generar una contraseña de aplicación
3. Usar esa contraseña de aplicación en `.env` (nunca la contraseña normal)

## Cómo Funciona un Ciclo

Cada vez que el timer dispara el servicio (`main.py`), ocurre lo siguiente:

1. **Limpiezas periódicas**: si corresponde, elimina registros de más de 30 días de la base de datos (una vez al día) y limpia el cache de Selenium (cada 7 días).
2. **Lectura de correos**: obtiene los correos **no leídos** del remitente en `SENDER_FILTER` recibidos en los **últimos 5 minutos**, y los marca como leídos al obtenerlos.
3. **Filtrado**: separa los correos que son solicitudes de reporte (contienen "REPORTE" en asunto o cuerpo) del resto.
4. **Procesamiento de cada correo restante**:
   - Extrae la URL que coincide con `LINK_PATTERN` (busca primero en el HTML, luego en el texto plano).
   - Si hay URL: abre la página con Selenium headless y hace clic en `BUTTON_SELECTOR`.
     - Éxito → registro `SUCCESS` en la base de datos.
     - Falla el clic → registro `FAILED`.
   - Si no hay URL válida: registro `NO_URL` (ya no se ignora silenciosamente).
   - Si ocurre una excepción durante el procesamiento: registro `ERROR`.
5. **Eliminación automática** (si `AUTO_DELETE_EMAILS=true`): tras cada uno de los casos anteriores (éxito, fallo, sin URL o error), el correo se elimina de la bandeja. Si está deshabilitado, el correo queda leído pero se mantiene en la bandeja.

## Funcionalidad de Reportes por Correo

Cualquier correo no leído (de cualquier remitente) cuyo asunto o cuerpo contenga la palabra **"REPORTE"** dispara el envío automático de un Excel con el historial de la base de datos (`export_to_excel`), enviado por SMTP al remitente de esa solicitud (`notifier.send_report_email`). Si `AUTO_DELETE_EMAILS=true`, el correo de solicitud se elimina tras enviar el reporte exitosamente.

## Eliminación Automática de Correos

Ver `AUTO_DELETE_EMAILS` en la tabla de variables. Comportamiento:

- **Valores que habilitan**: `true`, `1`, `yes`, `on`
- **Valores que deshabilitan**: `false`, `0`, `no`, `off` (o no configurar la variable)
- Se aplica a los cuatro desenlaces posibles de un correo procesado: `SUCCESS`, `FAILED`, `NO_URL` y `ERROR`
- Los correos eliminados **siguen registrados** en la base de datos; la eliminación solo afecta la bandeja de entrada
- Los correos eliminados **no se pueden recuperar** — deshabilita esta variable si necesitas auditar manualmente

## Gestión del Sistema

### Usando el Gestor Interactivo (timer — uso actual)

```bash
./gestionar_rpa_timer.sh
```

Permite ver el estado del timer y del servicio, ver logs (archivo y `journalctl`), iniciar/detener/reiniciar el timer, disparar una ejecución manual y ver las próximas ejecuciones programadas.

### Comandos Directos

**Verificar estado del timer:**
```bash
sudo systemctl status rpa_system.timer
```

**Ver próximas ejecuciones:**
```bash
sudo systemctl list-timers rpa_system.timer
```

**Iniciar / detener / reiniciar el timer:**
```bash
sudo systemctl start rpa_system.timer
sudo systemctl stop rpa_system.timer
sudo systemctl restart rpa_system.timer
```

**Disparar una ejecución manual (un solo ciclo):**
```bash
sudo systemctl start rpa_system.service
```

**Ver logs del servicio:**
```bash
sudo journalctl -u rpa_system.service -f
```

**Ver logs del archivo:**
```bash
tail -f rpa_system.log
```

### Ejecución Manual (fuera de systemd)

Para pruebas, ejecutando un solo ciclo directamente:

```bash
cd rpa && python3 main.py
```

## Frecuencia de Ejecución

El timer (`rpa_system.timer`) dispara el servicio **cada 30 segundos** (`OnCalendar=*:*:00/30`). Como cada ciclo solo procesa correos de los **últimos 5 minutos**, un correo puede procesarse en cualquiera de las ~10 ejecuciones siguientes a su llegada, pero nunca dos veces (queda marcado como leído tras la primera lectura).

## Monitoreo y Logs

### Archivos de Log

- **rpa_system.log**: log principal del sistema (crece sin rotación automática, ver "Mantenimiento")
- **journalctl**: logs del servicio systemd

### Comandos de Monitoreo

```bash
# Ver logs recientes
tail -20 rpa_system.log

# Ver logs en tiempo real
tail -f rpa_system.log

# Buscar errores
grep "ERROR" rpa_system.log

# Ver logs del servicio
sudo journalctl -u rpa_system.service -n 50
```

## Base de Datos

El sistema utiliza SQLite (`rpa_database.db`) para almacenar registros de correos procesados (éxitos, fallos, sin URL y errores), con remitente, asunto, link, estado, observaciones y marca de tiempo. Desde ahí se genera el Excel de reportes.

### Limpieza Automática

- Registros de base de datos con más de 30 días (una vez al día, controlado por `db_cleanup.flag`)
- Cache de Selenium (cada 7 días, controlado por `selenium_cleanup.flag`)

## Solución de Problemas

### Problemas Comunes

1. **Error de autenticación de correo:**
   - Verificar `EMAIL_ADDRESS` / `EMAIL_PASSWORD` en `.env`
   - Confirmar que se usa una contraseña de aplicación, no la contraseña normal

2. **Timeout en IMAP:**
   - Revisar logs para mensajes `Timeout obteniendo correos` / `Timeout marcando como leído` / `Timeout eliminando correo`
   - Aumentar `IMAP_TIMEOUT` en `.env` si la red es lenta

3. **Error de Selenium / clic fallido:**
   - Verificar que `BUTTON_SELECTOR` sigue siendo válido (Netflix puede cambiar el HTML del botón)
   - El sistema limpia automáticamente el cache de Selenium cada 7 días
   - Revisar logs para el detalle específico del error

4. **El timer no dispara ejecuciones:**
   ```bash
   sudo systemctl status rpa_system.timer
   sudo systemctl list-timers rpa_system.timer
   sudo journalctl -u rpa_system.service -n 20
   ```

5. **Espacio en disco:**
   - `rpa_system.log` no rota automáticamente y puede crecer mucho — ver "Mantenimiento"
   - Verificar cache de Selenium con: `du -sh ~/.cache/selenium/`

### Verificación de Funcionamiento

```bash
# Verificar que el timer está activo
sudo systemctl is-active rpa_system.timer

# Ver el resultado de la última ejecución
sudo systemctl status rpa_system.service

# Verificar logs recientes
tail -10 rpa_system.log
```

## Mantenimiento

### Limpieza Manual

```bash
# Limpiar cache de Selenium
rm -rf ~/.cache/selenium/chrome/linux64/*
rm -rf ~/.cache/selenium/chromedriver/linux64/*

# Truncar el log a las últimas 1000 líneas
tail -n 1000 rpa_system.log > rpa_system.log.tmp
mv rpa_system.log.tmp rpa_system.log
```

### Actualización

```bash
sudo systemctl stop rpa_system.timer
cp rpa_database.db rpa_database.db.backup
git pull
sudo cp rpa_system.service rpa_system.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start rpa_system.timer
```

## Seguridad

- El servicio corre con permisos de root, con `ProtectSystem=strict`, `PrivateTmp=true` y `NoNewPrivileges=true`, y solo puede escribir dentro de `ReadWritePaths=/root/automatizacion`
- Las credenciales se almacenan en `.env` (excluido del repositorio vía `.gitignore`), nunca las subas a git
- Los logs pueden contener asuntos y direcciones de correo — considerar su sensibilidad al compartir
- `AUTO_DELETE_EMAILS=true` elimina correos de forma permanente e irrecuperable

## Dependencias

Ver `requirements.txt`:

- pandas
- openpyxl
- python-dotenv
- imap-tools
- selenium
- webdriver-manager
- beautifulsoup4
- sqlite3 (incluido con Python)
