#!/bin/bash

# Script para gestionar el Sistema RPA con Timer
# Uso: ./gestionar_rpa_timer.sh

clear
echo "🎯 GESTOR DEL SISTEMA RPA (TIMER)"
echo "==================================="
echo ""

# Función para mostrar el estado del timer
mostrar_estado_timer() {
    echo "📊 Estado del Timer RPA:"
    sudo systemctl status rpa_system.timer --no-pager -l
    echo ""
}

# Función para mostrar el estado del servicio
mostrar_estado_servicio() {
    echo "📊 Estado del Servicio RPA:"
    sudo systemctl status rpa_system.service --no-pager -l
    echo ""
}

# Función para ver logs
ver_logs() {
    echo "📋 Últimos 10 logs del sistema:"
    sudo journalctl -u rpa_system.service -n 10 --no-pager
    echo ""
}

# Función para ver logs en tiempo real
logs_tiempo_real() {
    echo "🔍 Mostrando logs en tiempo real..."
    echo "Presiona Ctrl+C para salir"
    echo ""
    sudo journalctl -u rpa_system.service -f
}

# Función para detener el timer
detener_timer() {
    echo "⏹️ Deteniendo el timer RPA..."
    sudo systemctl stop rpa_system.timer
    echo "✅ Timer detenido"
    echo ""
}

# Función para iniciar el timer
iniciar_timer() {
    echo "▶️ Iniciando el timer RPA..."
    sudo systemctl start rpa_system.timer
    echo "✅ Timer iniciado"
    echo ""
}

# Función para reiniciar el timer
reiniciar_timer() {
    echo "🔄 Reiniciando el timer RPA..."
    sudo systemctl restart rpa_system.timer
    echo "✅ Timer reiniciado"
    echo ""
}

# Función para ejecutar manualmente
ejecutar_manual() {
    echo "🚀 Ejecutando RPA manualmente..."
    sudo systemctl start rpa_system.service
    echo "✅ Ejecución manual iniciada"
    echo ""
}

# Función para ver próximas ejecuciones
ver_proximas_ejecuciones() {
    echo "⏰ Próximas ejecuciones programadas:"
    sudo systemctl list-timers rpa_system.timer --no-pager
    echo ""
}

# Menú principal
while true; do
    echo "Selecciona una opción:"
    echo ""
    echo "1️⃣  Ver estado del timer"
    echo "2️⃣  Ver estado del servicio"
    echo "3️⃣  Ver logs recientes"
    echo "4️⃣  Ver logs en tiempo real"
    echo "5️⃣  Detener timer"
    echo "6️⃣  Iniciar timer"
    echo "7️⃣  Reiniciar timer"
    echo "8️⃣  Ejecutar manualmente"
    echo "9️⃣  Ver próximas ejecuciones"
    echo "🔟  Ver archivo de log"
    echo "1️⃣1️⃣  Salir"
    echo ""
    read -p "Ingresa el número de la opción: " opcion
    
    case $opcion in
        1)
            mostrar_estado_timer
            ;;
        2)
            mostrar_estado_servicio
            ;;
        3)
            ver_logs
            ;;
        4)
            logs_tiempo_real
            ;;
        5)
            detener_timer
            mostrar_estado_timer
            ;;
        6)
            iniciar_timer
            mostrar_estado_timer
            ;;
        7)
            reiniciar_timer
            mostrar_estado_timer
            ;;
        8)
            ejecutar_manual
            ;;
        9)
            ver_proximas_ejecuciones
            ;;
        10)
            echo "📄 Contenido del archivo de log:"
            tail -20 rpa_system.log 2>/dev/null || echo "Archivo de log no encontrado"
            echo ""
            ;;
        11)
            echo "👋 ¡Hasta luego!"
            exit 0
            ;;
        *)
            echo "❌ Opción no válida. Intenta de nuevo."
            echo ""
            ;;
    esac
    
    read -p "Presiona Enter para continuar..."
    clear
    echo "🎯 GESTOR DEL SISTEMA RPA (TIMER)"
    echo "==================================="
    echo ""
done 