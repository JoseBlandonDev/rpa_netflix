#!/bin/bash

# Script para desplegar el proyecto RPA a la VPS
# Uso: ./deploy_to_vps.sh [usuario@servidor]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Verificar argumentos
if [ $# -eq 0 ]; then
    print_error "Uso: $0 [usuario@servidor]"
    print_error "Ejemplo: $0 ubuntu@192.168.1.100"
    exit 1
fi

VPS_HOST="$1"
PROJECT_NAME="rpa-correo"
LOCAL_PATH="."
REMOTE_PATH="/opt/$PROJECT_NAME"

print_header "🚀 DESPLIEGUE DEL RPA A VPS"
echo "=================================="
echo "Servidor: $VPS_HOST"
echo "Proyecto: $PROJECT_NAME"
echo "Ruta local: $LOCAL_PATH"
echo "Ruta remota: $REMOTE_PATH"
echo ""

# Verificar conexión SSH
print_status "Verificando conexión SSH..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_HOST" exit 2>/dev/null; then
    print_error "No se puede conectar a $VPS_HOST"
    print_error "Verifica que:"
    print_error "1. La dirección IP/hostname es correcta"
    print_error "2. Las claves SSH están configuradas"
    print_error "3. El usuario tiene permisos de sudo"
    exit 1
fi

print_status "Conexión SSH exitosa ✅"

# Verificar que el servidor es Ubuntu
print_status "Verificando sistema operativo..."
if ! ssh "$VPS_HOST" "grep -q 'Ubuntu' /etc/os-release"; then
    print_error "El servidor no es Ubuntu"
    exit 1
fi

print_status "Sistema Ubuntu detectado ✅"

# Crear directorio temporal para el despliegue
TEMP_DIR="/tmp/rpa_deploy_$(date +%s)"
print_status "Creando directorio temporal: $TEMP_DIR"

# Crear archivo de exclusión para rsync
cat > /tmp/rsync_exclude.txt << 'EOF'
# Archivos de desarrollo
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Logs y datos
*.log
logs/
data/
backups/

# Archivos de configuración local
.env
.env.local
.env.production

# Archivos del sistema
.DS_Store
Thumbs.db
.vscode/
.idea/

# Git
.git/
.gitignore

# Archivos temporales
*.tmp
*.temp
*.swp
*.swo

# Archivos de backup
*.bak
*.backup

# Archivos de instalación
install_vps.sh
deploy_to_vps.sh
README_VPS.md
EOF

# Sincronizar archivos
print_status "Sincronizando archivos del proyecto..."
rsync -avz --progress \
    --exclude-from=/tmp/rsync_exclude.txt \
    --exclude='.git/' \
    --exclude='*.log' \
    --exclude='data/' \
    --exclude='backups/' \
    --exclude='venv/' \
    "$LOCAL_PATH/" \
    "$VPS_HOST:$TEMP_DIR/"

if [ $? -eq 0 ]; then
    print_status "Sincronización completada ✅"
else
    print_error "Error en la sincronización"
    exit 1
fi

# Ejecutar instalación en la VPS
print_status "Ejecutando instalación en la VPS..."
ssh "$VPS_HOST" << 'EOF'
    set -e
    
    # Mover archivos al directorio final
    sudo rm -rf /opt/rpa-correo
    sudo mv /tmp/rpa_deploy_* /opt/rpa-correo
    sudo chown -R $USER:$USER /opt/rpa-correo
    
    # Ejecutar script de instalación
    cd /opt/rpa-correo
    chmod +x install_vps.sh
    ./install_vps.sh
EOF

if [ $? -eq 0 ]; then
    print_status "Instalación completada ✅"
else
    print_error "Error en la instalación"
    exit 1
fi

# Limpiar archivos temporales
rm -f /tmp/rsync_exclude.txt

print_header "🎉 DESPLIEGUE COMPLETADO"
echo "=============================="
echo ""
echo "Próximos pasos en la VPS:"
echo ""
echo "1. Conectarse a la VPS:"
echo "   ssh $VPS_HOST"
echo ""
echo "2. Configurar credenciales:"
echo "   nano /opt/rpa-correo/.env"
echo ""
echo "3. Verificar configuración:"
echo "   cd /opt/rpa-correo"
echo "   ./manage_service.sh check"
echo ""
echo "4. Iniciar el servicio:"
echo "   ./manage_service.sh start"
echo ""
echo "5. Verificar estado:"
echo "   ./manage_service.sh status"
echo ""
echo "6. Ver logs en tiempo real:"
echo "   ./manage_service.sh logs"
echo ""
echo "Comandos útiles:"
echo "- ./manage_service.sh start|stop|restart|status"
echo "- ./monitor.sh (estado del sistema)"
echo "- ./backup.sh (backup manual)"
echo ""
echo "El RPA se ejecutará automáticamente en segundo plano"
echo "y se reiniciará automáticamente si se detiene." 