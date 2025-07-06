# 🚀 Guía de Despliegue en VPS Ubuntu 22.04

Esta guía te explica paso a paso cómo desplegar tu proyecto RPA en una VPS Ubuntu 22.04.

## 📋 Requisitos Previos

### En tu máquina local:
- Proyecto RPA configurado y funcionando
- Claves SSH configuradas para la VPS
- `rsync` instalado (normalmente viene por defecto)

### En la VPS:
- Ubuntu 22.04 LTS
- Usuario con permisos sudo
- Conexión a internet
- Mínimo 1GB RAM, 10GB disco

## 🔧 Preparación de la VPS

### 1. Conectarse a la VPS
```bash
ssh usuario@ip_de_tu_vps
```

### 2. Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Configurar usuario (si es necesario)
```bash
# Crear usuario si no existe
sudo adduser rpa_user
sudo usermod -aG sudo rpa_user

# Configurar SSH para el nuevo usuario
sudo mkdir -p /home/rpa_user/.ssh
sudo cp ~/.ssh/authorized_keys /home/rpa_user/.ssh/
sudo chown -R rpa_user:rpa_user /home/rpa_user/.ssh
```

## 🚀 Despliegue Automático

### Opción 1: Despliegue desde tu máquina local

1. **Desde tu máquina local**, ejecuta:
```bash
./deploy_to_vps.sh usuario@ip_de_tu_vps
```

**Ejemplo:**
```bash
./deploy_to_vps.sh ubuntu@192.168.1.100
```

2. **El script automáticamente:**
   - Verifica la conexión SSH
   - Sincroniza todos los archivos del proyecto
   - Instala todas las dependencias
   - Configura el servicio systemd
   - Configura monitoreo y backups

### Opción 2: Despliegue manual en la VPS

Si prefieres hacerlo manualmente:

1. **Subir archivos a la VPS:**
```bash
# Desde tu máquina local
rsync -avz --exclude='venv/' --exclude='*.log' --exclude='data/' ./ usuario@ip_de_tu_vps:/tmp/rpa-correo/
```

2. **En la VPS, ejecutar:**
```bash
sudo mv /tmp/rpa-correo /opt/
cd /opt/rpa-correo
chmod +x install_vps.sh
./install_vps.sh
```

## ⚙️ Configuración Post-Instalación

### 1. Configurar credenciales
```bash
# En la VPS
nano /opt/rpa-correo/.env
```

**Ejemplo de archivo .env:**
```env
# Configuración de Email
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_de_aplicacion
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Configuración de Base de Datos
DATABASE_PATH=/opt/rpa-correo/data/rpa_database.db

# Configuración de Logs
LOG_PATH=/opt/rpa-correo/logs
LOG_LEVEL=INFO

# Configuración de Selenium
HEADLESS=true
DEBUG=false
```

### 2. Verificar configuración
```bash
cd /opt/rpa-correo
./manage_service.sh check
```

### 3. Iniciar el servicio
```bash
./manage_service.sh start
```

## 🛠️ Gestión del Servicio

### Comandos principales:
```bash
# Iniciar servicio
./manage_service.sh start

# Detener servicio
./manage_service.sh stop

# Reiniciar servicio
./manage_service.sh restart

# Ver estado
./manage_service.sh status

# Ver logs en tiempo real
./manage_service.sh logs

# Ver logs recientes
./manage_service.sh logs-recent

# Verificar configuración
./manage_service.sh check
```

### Monitoreo del sistema:
```bash
# Ver estado general
./monitor.sh

# Ver uso de recursos
htop

# Ver espacio en disco
df -h
```

## 📊 Logs y Monitoreo

### Ubicación de logs:
- **Logs del servicio:** `/var/log/syslog` (filtrado por `journalctl -u rpa-correo`)
- **Logs de la aplicación:** `/opt/rpa-correo/logs/`
- **Logs del sistema:** `/var/log/`

### Ver logs en tiempo real:
```bash
# Logs del servicio systemd
sudo journalctl -u rpa-correo -f

# Logs de la aplicación
tail -f /opt/rpa-correo/logs/rpa_background.log

# Logs del sistema
tail -f /var/log/syslog | grep rpa-correo
```

## 🔄 Backups Automáticos

### Configuración automática:
- Los backups se crean automáticamente cada día a las 2:00 AM
- Se mantienen los últimos 5 backups
- Ubicación: `/opt/rpa-correo/backups/`

### Backup manual:
```bash
cd /opt/rpa-correo
./backup.sh
```

### Restaurar backup:
```bash
# Descomprimir backup
tar -xzf /opt/rpa-correo/backups/rpa_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/

# Restaurar archivos
sudo cp -r /tmp/opt/rpa-correo/* /opt/rpa-correo/
sudo chown -R $USER:$USER /opt/rpa-correo
```

## 🔧 Solución de Problemas

### Problema: Servicio no inicia
```bash
# Verificar estado
sudo systemctl status rpa-correo

# Ver logs detallados
sudo journalctl -u rpa-correo -n 50

# Verificar configuración
./manage_service.sh check
```

### Problema: Error de permisos
```bash
# Corregir permisos
sudo chown -R $USER:$USER /opt/rpa-correo
chmod +x /opt/rpa-correo/src/main.py
```

### Problema: Chrome/ChromeDriver no funciona
```bash
# Reinstalar Chrome
sudo apt remove google-chrome-stable
sudo apt install google-chrome-stable

# Reinstalar ChromeDriver
sudo rm /usr/local/bin/chromedriver
# El script de instalación lo reinstalará automáticamente
```

### Problema: Memoria insuficiente
```bash
# Ver uso de memoria
free -h

# Optimizar configuración
# Editar /opt/rpa-correo/src/main.py y cambiar HEADLESS=True
```

## 🔒 Seguridad

### Firewall configurado:
- SSH (puerto 22)
- HTTP (puerto 80)
- HTTPS (puerto 443)

### Permisos de archivos:
- Archivos de configuración: 600
- Scripts ejecutables: 755
- Directorios: 755

### Usuario del servicio:
- Usuario dedicado: `rpa_user`
- Sin acceso shell directo
- Permisos mínimos necesarios

## 📈 Monitoreo y Alertas

### Monitoreo automático:
- Estado del servicio cada 5 minutos
- Uso de recursos del sistema
- Espacio en disco
- Logs de errores

### Alertas recomendadas:
- Configurar notificaciones por email
- Monitoreo de uptime
- Alertas de uso de recursos

## 🔄 Actualizaciones

### Actualizar el proyecto:
```bash
# Desde tu máquina local
./deploy_to_vps.sh usuario@ip_de_tu_vps

# O manualmente en la VPS
cd /opt/rpa-correo
git pull origin main
./manage_service.sh restart
```

### Actualizar dependencias:
```bash
cd /opt/rpa-correo
source venv/bin/activate
pip install -r requirements.txt --upgrade
./manage_service.sh restart
```

## 📞 Soporte

### Información útil para debugging:
```bash
# Información del sistema
uname -a
lsb_release -a

# Información del servicio
systemctl show rpa-correo

# Información de Python
python3 --version
pip list

# Información de Chrome
google-chrome --version
chromedriver --version
```

### Archivos importantes:
- **Configuración:** `/opt/rpa-correo/.env`
- **Logs:** `/opt/rpa-correo/logs/`
- **Base de datos:** `/opt/rpa-correo/data/`
- **Scripts:** `/opt/rpa-correo/manage_service.sh`

---

## ✅ Checklist de Despliegue

- [ ] VPS Ubuntu 22.04 configurada
- [ ] Claves SSH configuradas
- [ ] Proyecto desplegado con `deploy_to_vps.sh`
- [ ] Archivo `.env` configurado con credenciales
- [ ] Servicio iniciado y funcionando
- [ ] Logs verificados sin errores
- [ ] Backup automático configurado
- [ ] Monitoreo funcionando
- [ ] Firewall configurado
- [ ] Documentación actualizada

¡Tu RPA está listo para funcionar 24/7 en la VPS! 🎉 