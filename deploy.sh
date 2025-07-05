#!/bin/bash

# Script de despliegue para VPS
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando despliegue del RPA en VPS..."
echo "=========================================="

# Verificar si estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Este script está diseñado para Linux"
    exit 1
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
sudo apt install -y python3 python3-pip python3-venv chromium-browser xvfb git curl

# Crear directorio del proyecto si no existe
PROJECT_DIR="/opt/rpa_correo"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Creando directorio del proyecto..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR"
fi

# Navegar al directorio del proyecto
cd "$PROJECT_DIR"

# Clonar repositorio (si no existe)
if [ ! -d ".git" ]; then
    echo "📥 Clonando repositorio..."
    # Reemplaza con tu URL del repositorio
    git clone <TU_REPOSITORIO_URL> .
fi

# Crear entorno virtual
echo "🐍 Configurando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias de Python
echo "📚 Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Configurando archivo .env..."
    cp env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales reales"
    echo "   nano .env"
fi

# Crear directorio de logs
mkdir -p logs

# Dar permisos de ejecución
chmod +x src/main.py

# Crear servicio systemd para ejecución automática
echo "🔧 Configurando servicio systemd..."
sudo tee /etc/systemd/system/rpa-correo.service > /dev/null <<EOF
[Unit]
Description=RPA Sistema de Automatización de Correos
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable rpa-correo.service

echo "✅ Despliegue completado!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Edita el archivo .env con tus credenciales:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Inicia el servicio:"
echo "   sudo systemctl start rpa-correo.service"
echo ""
echo "3. Verifica el estado:"
echo "   sudo systemctl status rpa-correo.service"
echo ""
echo "4. Ver logs en tiempo real:"
echo "   sudo journalctl -u rpa-correo.service -f"
echo ""
echo "5. Para detener el servicio:"
echo "   sudo systemctl stop rpa-correo.service"
echo ""
echo "🎉 ¡El RPA está listo para funcionar!" 