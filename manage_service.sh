#!/bin/bash

# Script de gestión del servicio RPA
# Uso: ./manage_service.sh [start|stop|restart|status|logs|enable|disable]

SERVICE_NAME="rpa-correo.service"
PROJECT_DIR="/opt/rpa_correo"

case "$1" in
    start)
        echo "🚀 Iniciando servicio RPA..."
        sudo systemctl start $SERVICE_NAME
        echo "✅ Servicio iniciado"
        ;;
    stop)
        echo "🛑 Deteniendo servicio RPA..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Servicio detenido"
        ;;
    restart)
        echo "🔄 Reiniciando servicio RPA..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Servicio reiniciado"
        ;;
    status)
        echo "📊 Estado del servicio RPA:"
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "📋 Mostrando logs del servicio RPA:"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    logs-recent)
        echo "📋 Mostrando logs recientes del servicio RPA:"
        sudo journalctl -u $SERVICE_NAME -n 50
        ;;
    enable)
        echo "✅ Habilitando inicio automático del servicio RPA..."
        sudo systemctl enable $SERVICE_NAME
        echo "✅ Servicio habilitado para inicio automático"
        ;;
    disable)
        echo "❌ Deshabilitando inicio automático del servicio RPA..."
        sudo systemctl disable $SERVICE_NAME
        echo "✅ Servicio deshabilitado"
        ;;
    check-logs)
        echo "📋 Verificando archivos de log del RPA:"
        if [ -d "$PROJECT_DIR/logs" ]; then
            echo "Logs disponibles:"
            ls -la "$PROJECT_DIR/logs/"
            echo ""
            echo "Últimas líneas del log principal:"
            tail -n 20 "$PROJECT_DIR/logs/rpa_automation_$(date +%Y%m%d).log" 2>/dev/null || echo "No hay logs disponibles"
        else
            echo "Directorio de logs no encontrado"
        fi
        ;;
    check-db)
        echo "🗄️ Verificando base de datos:"
        if [ -f "$PROJECT_DIR/rpa.db" ]; then
            echo "Base de datos encontrada:"
            ls -la "$PROJECT_DIR/rpa.db"
            echo ""
            echo "Registros en la base de datos:"
            sqlite3 "$PROJECT_DIR/rpa.db" "SELECT COUNT(*) as total_records FROM rpa_records;" 2>/dev/null || echo "Error al consultar base de datos"
        else
            echo "Base de datos no encontrada"
        fi
        ;;
    check)
        echo "🔍 Verificación completa del sistema RPA:"
        echo "========================================"
        echo ""
        
        # Verificar archivo .env
        echo "📋 Verificando configuración (.env):"
        if [ -f ".env" ]; then
            echo "✅ Archivo .env encontrado"
            if grep -q "EMAIL_USER" .env && grep -q "EMAIL_PASSWORD" .env; then
                echo "✅ Credenciales de email configuradas"
            else
                echo "⚠️  Credenciales de email no encontradas"
            fi
        else
            echo "❌ Archivo .env no encontrado"
        fi
        echo ""
        
        # Verificar Python y dependencias
        echo "🐍 Verificando Python y dependencias:"
        if command -v python3 &> /dev/null; then
            echo "✅ Python3 instalado: $(python3 --version)"
        else
            echo "❌ Python3 no encontrado"
        fi
        
        if [ -d "venv" ]; then
            echo "✅ Entorno virtual encontrado"
            source venv/bin/activate
            if pip list | grep -q selenium; then
                echo "✅ Selenium instalado"
            else
                echo "❌ Selenium no encontrado"
            fi
        else
            echo "❌ Entorno virtual no encontrado"
        fi
        echo ""
        
        # Verificar Chrome y ChromeDriver
        echo "🌐 Verificando Chrome y ChromeDriver:"
        if command -v google-chrome &> /dev/null; then
            echo "✅ Chrome instalado: $(google-chrome --version)"
        else
            echo "❌ Chrome no encontrado"
        fi
        
        if command -v chromedriver &> /dev/null; then
            echo "✅ ChromeDriver instalado: $(chromedriver --version)"
        else
            echo "❌ ChromeDriver no encontrado"
        fi
        echo ""
        
        # Verificar directorios
        echo "📁 Verificando directorios:"
        if [ -d "logs" ]; then
            echo "✅ Directorio logs encontrado"
        else
            echo "❌ Directorio logs no encontrado"
        fi
        
        if [ -d "data" ]; then
            echo "✅ Directorio data encontrado"
        else
            echo "❌ Directorio data no encontrado"
        fi
        echo ""
        
        # Verificar archivos principales
        echo "📄 Verificando archivos principales:"
        if [ -f "src/main.py" ]; then
            echo "✅ main.py encontrado"
        else
            echo "❌ main.py no encontrado"
        fi
        
        if [ -f "requirements.txt" ]; then
            echo "✅ requirements.txt encontrado"
        else
            echo "❌ requirements.txt no encontrado"
        fi
        echo ""
        
        # Verificar servicio systemd
        echo "⚙️ Verificando servicio systemd:"
        if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
            echo "✅ Archivo de servicio encontrado"
        else
            echo "❌ Archivo de servicio no encontrado"
        fi
        
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo "✅ Servicio está activo"
        else
            echo "⚠️  Servicio no está activo"
        fi
        echo ""
        
        echo "🔍 Verificación completada"
        ;;
    *)
        echo "❌ Uso: $0 {start|stop|restart|status|logs|logs-recent|enable|disable|check-logs|check-db|check}"
        echo ""
        echo "Comandos disponibles:"
        echo "  start       - Iniciar el servicio"
        echo "  stop        - Detener el servicio"
        echo "  restart     - Reiniciar el servicio"
        echo "  status      - Ver estado del servicio"
        echo "  logs        - Ver logs en tiempo real"
        echo "  logs-recent - Ver logs recientes"
        echo "  enable      - Habilitar inicio automático"
        echo "  disable     - Deshabilitar inicio automático"
        echo "  check-logs  - Verificar archivos de log"
        echo "  check-db    - Verificar base de datos"
        echo "  check       - Verificación completa del sistema"
        exit 1
        ;;
esac 