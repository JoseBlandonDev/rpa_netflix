# 🚀 RPA Email Automation - Guía de Instalación en VPS

Guía completa para instalar y configurar el sistema RPA de automatización de correos en un VPS Ubuntu 22.04 LTS.

## 📋 Requisitos del VPS

- **Sistema Operativo**: Ubuntu 22.04 LTS
- **RAM**: Mínimo 1GB (recomendado 2GB+)
- **Almacenamiento**: Mínimo 10GB libre
- **Conexión**: Internet estable
- **Usuario**: Acceso sudo

## 🛠️ Instalación Automática

### Opción 1: Instalación con Script Automático (Recomendado)

```bash
# 1. Descargar el proyecto
git clone <tu-repositorio> rpa_correo
cd rpa_correo

# 2. Dar permisos de ejecución
chmod +x install_vps.sh
chmod +x manage_service.sh

# 3. Ejecutar instalación automática
./install_vps.sh
```

### Opción 2: Instalación Manual

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv chromium-browser xvfb git

# 3. Crear directorio del proyecto
sudo mkdir -p /opt/rpa_correo
sudo chown $USER:$USER /opt/rpa_correo
cd /opt/rpa_correo

# 4. Configurar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 5. Instalar dependencias Python
pip install -r requirements.txt

# 6. Configurar archivo .env
cp env.example .env
nano .env  # Editar con tus credenciales

# 7. Configurar servicio
sudo cp rpa-correo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rpa-correo.service
```

## ⚙️ Configuración del Archivo .env

Edita el archivo `.env` con tus credenciales reales:

```env
# Email configuration
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_contraseña_de_aplicacion
IMAP_SERVER=imap.gmail.com

# Email filters
SENDER_FILTER=remitente@ejemplo.com
URL_PATTERN=https://ejemplo.com

# Web automation configuration
BUTTON_SELECTOR=//button | //a[contains(text(), 'Click')]
SELECTOR_TYPE=xpath
HEADLESS_MODE=true

# Debug and logging
DEBUG_MODE=false
LOG_LEVEL=INFO
```

## 🎮 Gestión del Servicio

### Comandos Básicos

```bash
# Iniciar el servicio
./manage_service.sh start

# Detener el servicio
./manage_service.sh stop

# Reiniciar el servicio
./manage_service.sh restart

# Ver estado
./manage_service.sh status

# Ver logs en tiempo real
./manage_service.sh logs

# Ver logs recientes
./manage_service.sh logs-recent
```

### Comandos Avanzados

```bash
# Habilitar inicio automático
./manage_service.sh enable

# Deshabilitar inicio automático
./manage_service.sh disable

# Verificar archivos de log
./manage_service.sh check-logs

# Verificar base de datos
./manage_service.sh check-db
```

## 📊 Monitoreo y Logs

### Logs del Sistema

```bash
# Logs del servicio systemd
sudo journalctl -u rpa-correo.service -f

# Logs específicos del RPA
tail -f /opt/rpa_correo/logs/rpa_automation_$(date +%Y%m%d).log

# Logs de errores
tail -f /opt/rpa_correo/logs/rpa_errors_$(date +%Y%m%d).log
```

### Verificar Estado

```bash
# Estado del servicio
sudo systemctl is-active rpa-correo.service

# Estadísticas detalladas
sudo systemctl status rpa-correo.service

# Verificar recursos
htop
free -h
df -h
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. Servicio no inicia
```bash
# Verificar logs de error
sudo journalctl -u rpa-correo.service -n 50

# Verificar permisos
ls -la /opt/rpa_correo/
sudo chown -R ubuntu:ubuntu /opt/rpa_correo/
```

#### 2. Error de Chrome/Chromium
```bash
# Instalar dependencias adicionales
sudo apt install -y xvfb

# Verificar instalación de Chromium
which chromium-browser
```

#### 3. Error de credenciales
```bash
# Verificar archivo .env
cat /opt/rpa_correo/.env

# Probar conexión manual
cd /opt/rpa_correo
source venv/bin/activate
python3 src/sub/email_reader.py
```

#### 4. Error de permisos
```bash
# Corregir permisos
sudo chown -R ubuntu:ubuntu /opt/rpa_correo/
chmod +x /opt/rpa_correo/src/main.py
chmod 755 /opt/rpa_correo/logs/
```

### Comandos de Diagnóstico

```bash
# Verificar estructura del proyecto
tree /opt/rpa_correo/

# Verificar entorno virtual
/opt/rpa_correo/venv/bin/python --version

# Verificar dependencias
/opt/rpa_correo/venv/bin/pip list

# Verificar configuración del servicio
sudo systemctl cat rpa-correo.service
```

## 🔒 Seguridad

### Configuraciones de Seguridad

- ✅ **Ejecución con usuario específico** (no root)
- ✅ **Límites de recursos** (1GB RAM, 50% CPU)
- ✅ **Protección del sistema** (ReadWritePaths limitados)
- ✅ **Logs seguros** (sin credenciales expuestas)

### Mantenimiento

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Limpiar logs antiguos
sudo journalctl --vacuum-time=7d

# Verificar espacio en disco
df -h

# Verificar uso de memoria
free -h
```

## 📈 Monitoreo de Rendimiento

### Métricas Importantes

- **Uso de CPU**: Máximo 50% configurado
- **Uso de RAM**: Máximo 1GB configurado
- **Espacio en disco**: Monitorear logs y base de datos
- **Conexiones de red**: Monitorear conexiones IMAP

### Alertas Recomendadas

- Servicio caído por más de 5 minutos
- Uso de memoria superior al 80%
- Espacio en disco inferior al 20%
- Errores consecutivos en logs

## 🆘 Soporte

### Información Útil para Troubleshooting

```bash
# Información del sistema
uname -a
lsb_release -a

# Información del servicio
sudo systemctl status rpa-correo.service

# Logs del sistema
sudo journalctl -xe

# Estado de la red
ping -c 3 8.8.8.8
```

### Archivos de Configuración Importantes

- `/etc/systemd/system/rpa-correo.service` - Configuración del servicio
- `/opt/rpa_correo/.env` - Variables de entorno
- `/opt/rpa_correo/logs/` - Archivos de log
- `/opt/rpa_correo/rpa.db` - Base de datos SQLite

---

**¡El sistema está listo para funcionar 24/7 en tu VPS!** 🎉 