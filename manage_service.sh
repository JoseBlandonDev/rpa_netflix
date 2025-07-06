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
    *)
        echo "❌ Uso: $0 {start|stop|restart|status|logs|logs-recent|enable|disable|check-logs|check-db}"
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
        exit 1
        ;;
esac 