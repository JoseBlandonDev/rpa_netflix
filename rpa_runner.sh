#!/bin/bash

# Script para ejecutar el sistema RPA en background
# Ubicación: /root/rpa_system/rpa_runner.sh

# Cambiar al directorio del proyecto
cd /root/rpa_system

# Verificar que existe el archivo principal
if [ ! -f "rpa/main.py" ]; then
    echo "Error: No se encuentra rpa/main.py"
    exit 1
fi

# Lockfile para evitar ejecuciones simultáneas
LOCKFILE="/tmp/rpa_system.lock"

# Verificar si ya hay una ejecución en curso
if [ -f "$LOCKFILE" ]; then
    PID=$(cat "$LOCKFILE" 2>/dev/null)
    if kill -0 "$PID" 2>/dev/null; then
        echo "RPA ya está ejecutándose (PID: $PID)"
        exit 0
    else
        # El proceso ya no existe, eliminar lockfile obsoleto
        rm -f "$LOCKFILE"
    fi
fi

# Crear lockfile con el PID actual
echo $$ > "$LOCKFILE"

# Función para limpiar el lockfile al salir
cleanup() {
    rm -f "$LOCKFILE"
    exit 0
}

# Capturar señales para limpiar el lockfile
trap cleanup EXIT INT TERM

# Ejecutar el sistema RPA
python3 rpa/main.py >> rpa_system.log 2>&1 