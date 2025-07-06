#!/bin/bash

# Script de instalación para VPS Ubuntu 22.04
# Este script instala todas las dependencias necesarias para el RPA

set -e  # Salir si hay algún error

echo "🚀 Iniciando instalación del RPA en VPS Ubuntu 22.04..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    print_error "Este script está diseñado para Ubuntu. Sistema detectado: $(cat /etc/os-release | grep PRETTY_NAME)"
    exit 1
fi

print_status "Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

print_status "Instalando dependencias del sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

print_status "Instalando Chrome y ChromeDriver..."
# Agregar repositorio de Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

sudo apt update
sudo apt install -y google-chrome-stable

# Instalar ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | awk -F'.' '{print $1}')
print_status "Versión de Chrome detectada: $CHROME_VERSION"

# Descargar ChromeDriver compatible
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
print_status "Descargando ChromeDriver versión: $CHROMEDRIVER_VERSION"

wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip /tmp/chromedriver.zip -d /tmp/
sudo mv /tmp/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

print_status "Creando directorio del proyecto..."
sudo mkdir -p /opt/rpa-correo
sudo chown $USER:$USER /opt/rpa-correo

print_status "Creando entorno virtual Python..."
cd /opt/rpa-correo
python3 -m venv venv
source venv/bin/activate

print_status "Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "Configurando permisos..."
sudo chown -R $USER:$USER /opt/rpa-correo
chmod +x /opt/rpa-correo/src/main.py

print_status "Creando directorios de logs y datos..."
mkdir -p /opt/rpa-correo/logs
mkdir -p /opt/rpa-correo/data

print_status "Configurando systemd service..."
sudo cp rpa-correo.service /etc/systemd/system/
sudo systemctl daemon-reload

print_status "Configurando firewall (opcional)..."
# Permitir conexiones SSH y HTTP/HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

print_status "Configurando monitoreo del sistema..."
# Instalar htop para monitoreo
sudo apt install -y htop

print_status "Creando script de gestión..."
cat > /opt/rpa-correo/manage_service.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="rpa-correo"
PROJECT_PATH="/opt/rpa-correo"

case "$1" in
    start)
        echo "Iniciando servicio RPA..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl enable $SERVICE_NAME
        ;;
    stop)
        echo "Deteniendo servicio RPA..."
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl disable $SERVICE_NAME
        ;;
    restart)
        echo "Reiniciando servicio RPA..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        echo "Estado del servicio RPA:"
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "Mostrando logs del servicio:"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    logs-recent)
        echo "Logs recientes:"
        sudo journalctl -u $SERVICE_NAME --since "1 hour ago"
        ;;
    check)
        echo "Verificando configuración..."
        cd $PROJECT_PATH
        source venv/bin/activate
        python3 vps_config.py
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|logs-recent|check}"
        exit 1
        ;;
esac
EOF

chmod +x /opt/rpa-correo/manage_service.sh

print_status "Configurando variables de entorno..."
if [ ! -f /opt/rpa-correo/.env ]; then
    print_warning "Archivo .env no encontrado. Debes crearlo manualmente con tus credenciales."
    print_status "Ejemplo de archivo .env:"
    cat > /opt/rpa-correo/.env.example << 'EOF'
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
EOF
fi

print_status "Configurando rotación de logs..."
sudo tee /etc/logrotate.d/rpa-correo > /dev/null << 'EOF'
/opt/rpa-correo/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload rpa-correo
    endscript
}
EOF

print_status "Configurando monitoreo de recursos..."
# Crear script de monitoreo
cat > /opt/rpa-correo/monitor.sh << 'EOF'
#!/bin/bash

echo "=== MONITOREO DEL SISTEMA RPA ==="
echo "Fecha: $(date)"
echo ""

echo "Estado del servicio:"
systemctl is-active rpa-correo

echo ""
echo "Uso de CPU y memoria:"
ps aux | grep python | grep main.py

echo ""
echo "Espacio en disco:"
df -h /opt/rpa-correo

echo ""
echo "Logs recientes:"
tail -n 10 /opt/rpa-correo/logs/rpa_background.log 2>/dev/null || echo "No hay logs disponibles"
EOF

chmod +x /opt/rpa-correo/monitor.sh

print_status "Configurando backup automático..."
# Crear script de backup
cat > /opt/rpa-correo/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/rpa-correo/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="rpa_backup_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

echo "Creando backup: $BACKUP_FILE"
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude='venv' \
    --exclude='*.log' \
    --exclude='backups' \
    /opt/rpa-correo

echo "Backup creado: $BACKUP_DIR/$BACKUP_FILE"

# Mantener solo los últimos 5 backups
ls -t $BACKUP_DIR/rpa_backup_*.tar.gz | tail -n +6 | xargs -r rm
EOF

chmod +x /opt/rpa-correo/backup.sh

# Agregar backup diario al crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/rpa-correo/backup.sh") | crontab -

echo ""
echo "🎉 INSTALACIÓN COMPLETADA"
echo "=========================="
echo ""
echo "Próximos pasos:"
echo "1. Copia tu archivo .env con las credenciales a /opt/rpa-correo/.env"
echo "2. Verifica la configuración: ./manage_service.sh check"
echo "3. Inicia el servicio: ./manage_service.sh start"
echo "4. Monitorea el estado: ./manage_service.sh status"
echo "5. Ver logs: ./manage_service.sh logs"
echo ""
echo "Comandos útiles:"
echo "- ./manage_service.sh start|stop|restart|status"
echo "- ./monitor.sh (para ver estado del sistema)"
echo "- ./backup.sh (para crear backup manual)"
echo ""
echo "El servicio se ejecutará automáticamente en modo headless"
echo "y se reiniciará automáticamente si se detiene." 