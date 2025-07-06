#!/bin/bash

# Script de verificación para el despliegue en VPS
# Verifica que todos los archivos necesarios estén presentes y configurados

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "🔍 VERIFICACIÓN DE DESPLIEGUE"
echo "============================="
echo ""

# Contador de errores
ERRORS=0
WARNINGS=0

# Verificar archivos esenciales
print_header "Verificando archivos esenciales..."

ESSENTIAL_FILES=(
    "src/main.py"
    "src/sub/email_reader.py"
    "src/sub/database.py"
    "src/sub/driver_web.py"
    "src/sub/logger.py"
    "src/sub/error_handler.py"
    "requirements.txt"
    "rpa-correo.service"
    "install_vps.sh"
    "deploy_to_vps.sh"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status "$file existe"
    else
        print_error "$file NO existe"
        ((ERRORS++))
    fi
done

echo ""

# Verificar archivos de configuración
print_header "Verificando archivos de configuración..."

if [ -f ".env" ]; then
    print_status "Archivo .env existe"
    
    # Verificar variables críticas
    if grep -q "EMAIL_USER" .env && grep -q "EMAIL_PASSWORD" .env; then
        print_status "Credenciales de email configuradas"
    else
        print_warning "Credenciales de email no encontradas en .env"
        ((WARNINGS++))
    fi
else
    print_warning "Archivo .env no existe (se creará en la VPS)"
    ((WARNINGS++))
fi

echo ""

# Verificar dependencias Python
print_header "Verificando dependencias Python..."

if [ -f "requirements.txt" ]; then
    REQUIRED_PACKAGES=(
        "selenium"
        "python-dotenv"
        "sqlite3"
        "imaplib"
        "email"
        "logging"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if grep -q "$package" requirements.txt; then
            print_status "$package en requirements.txt"
        else
            print_warning "$package no encontrado en requirements.txt"
            ((WARNINGS++))
        fi
    done
else
    print_error "requirements.txt no existe"
    ((ERRORS++))
fi

echo ""

# Verificar scripts de instalación
print_header "Verificando scripts de instalación..."

if [ -x "install_vps.sh" ]; then
    print_status "install_vps.sh es ejecutable"
else
    print_error "install_vps.sh no es ejecutable"
    ((ERRORS++))
fi

if [ -x "deploy_to_vps.sh" ]; then
    print_status "deploy_to_vps.sh es ejecutable"
else
    print_error "deploy_to_vps.sh no es ejecutable"
    ((ERRORS++))
fi

echo ""

# Verificar servicio systemd
print_header "Verificando configuración del servicio..."

if [ -f "rpa-correo.service" ]; then
    print_status "Archivo de servicio systemd existe"
    
    # Verificar configuración básica del servicio
    if grep -q "ExecStart" rpa-correo.service && grep -q "Restart" rpa-correo.service; then
        print_status "Configuración básica del servicio correcta"
    else
        print_warning "Configuración del servicio puede estar incompleta"
        ((WARNINGS++))
    fi
else
    print_error "Archivo rpa-correo.service no existe"
    ((ERRORS++))
fi

echo ""

# Verificar estructura del proyecto
print_header "Verificando estructura del proyecto..."

if [ -d "src" ] && [ -d "src/sub" ]; then
    print_status "Estructura de directorios correcta"
else
    print_error "Estructura de directorios incorrecta"
    ((ERRORS++))
fi

echo ""

# Verificar permisos
print_header "Verificando permisos..."

if [ -r "src/main.py" ] && [ -x "src/main.py" ]; then
    print_status "main.py tiene permisos correctos"
else
    print_warning "main.py puede necesitar permisos de ejecución"
    ((WARNINGS++))
fi

echo ""

# Verificar configuración de VPS
print_header "Verificando configuración específica de VPS..."

if [ -f "vps_config.py" ]; then
    print_status "Configuración específica de VPS existe"
else
    print_warning "Archivo vps_config.py no existe"
    ((WARNINGS++))
fi

echo ""

# Verificar documentación
print_header "Verificando documentación..."

if [ -f "README_DEPLOY.md" ]; then
    print_status "Documentación de despliegue existe"
else
    print_warning "README_DEPLOY.md no existe"
    ((WARNINGS++))
fi

echo ""

# Resumen final
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "=========================="
echo ""

if [ $ERRORS -eq 0 ]; then
    print_status "No se encontraron errores críticos"
else
    print_error "Se encontraron $ERRORS errores críticos"
fi

if [ $WARNINGS -eq 0 ]; then
    print_status "No se encontraron advertencias"
else
    print_warning "Se encontraron $WARNINGS advertencias"
fi

echo ""

if [ $ERRORS -eq 0 ]; then
    echo "🎉 ¡El proyecto está listo para el despliegue!"
    echo ""
    echo "Próximos pasos:"
    echo "1. Asegúrate de tener las claves SSH configuradas"
    echo "2. Ejecuta: ./deploy_to_vps.sh usuario@ip_de_tu_vps"
    echo "3. Configura las credenciales en la VPS"
    echo "4. Inicia el servicio"
    echo ""
    echo "Para más información, consulta README_DEPLOY.md"
else
    echo "❌ Corrige los errores antes del despliegue"
    echo ""
    echo "Errores encontrados:"
    echo "- Revisa los archivos faltantes"
    echo "- Verifica los permisos de ejecución"
    echo "- Asegúrate de que todos los archivos estén presentes"
fi

echo ""
echo "📋 Checklist rápido:"
echo "- [ ] Archivos esenciales presentes"
echo "- [ ] Scripts ejecutables"
echo "- [ ] Configuración del servicio"
echo "- [ ] Dependencias listadas"
echo "- [ ] Documentación disponible"
echo "- [ ] Claves SSH configuradas"
echo "- [ ] VPS Ubuntu 22.04 lista"

exit $ERRORS 