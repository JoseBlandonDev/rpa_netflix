"""
Configuración específica para VPS Ubuntu 22.04
Este archivo contiene las variables de entorno necesarias para ejecutar el RPA en la VPS
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la VPS
VPS_CONFIG = {
    'headless': True,  # Ejecutar sin interfaz gráfica en VPS
    'debug': False,    # Desactivar debug en producción
    'log_level': 'INFO',
    'max_retries': 3,
    'retry_delay': 5,
    'execution_interval': 600,  # 10 minutos
}

# Variables de entorno requeridas
REQUIRED_ENV_VARS = [
    'EMAIL_USER',
    'EMAIL_PASSWORD', 
    'IMAP_SERVER',
    'IMAP_PORT',
    'DATABASE_PATH',
    'LOG_PATH'
]

def validate_vps_config():
    """Valida que todas las variables de entorno estén configuradas"""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
    
    return True

if __name__ == "__main__":
    try:
        validate_vps_config()
        print("✅ Configuración VPS válida")
    except ValueError as e:
        print(f"❌ Error en configuración: {e}")
        exit(1) 