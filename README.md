# RPA Sistema de Automatización de Correos

Sistema de automatización RPA que lee correos electrónicos, extrae enlaces y ejecuta acciones web automáticamente.

## 🚀 Características

- Lectura automática de correos desde servidor IMAP
- Extracción de enlaces de correos
- Automatización web con Selenium
- Registro de resultados en base de datos SQLite
- Ejecución continua con intervalos configurables
- Modo headless para servidores VPS

## 📋 Requisitos

- Python 3.8+
- Chrome/Chromium browser
- Acceso a servidor IMAP
- VPS con Linux (recomendado Ubuntu/Debian)

## 🛠️ Instalación en VPS

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd rpa_correo
```

### 2. Instalar dependencias del sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv chromium-browser

# CentOS/RHEL
sudo yum install -y python3 python3-pip chromium
```

### 3. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar dependencias de Python
```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno
Crear archivo `.env` en la raíz del proyecto:
```bash
# Credenciales de correo
USUARIO_CORREO=tu_email@gmail.com
CLAVE_CORREO=tu_contraseña_de_aplicacion
IMAP_SERVIDOR=imap.gmail.com
FILTRO_REMITENTE=remitente@ejemplo.com

# Configuración de automatización web
SELECTOR_BOTON=//button | //a[contains(text(), 'Click')]
TIPO_SELECTOR=xpath
MODO_HEADLESS=true

# Configuración opcional
TEXTO_BOTON_URL=Click here
PATRON_URL=https://ejemplo.com
```

## 🚀 Uso

### Ejecución única
```bash
# Modo headless (producción)
python src/main.py
```

### Ejecución continua
```bash
# Modo headless (recomendado para VPS)
python src/main.py
```

## 📊 Monitoreo

### Logs
Los logs se guardan en el directorio `logs/` con formato:
```
logs/rpa_vps_YYYYMMDD.log
```

### Base de datos
Los resultados se almacenan en `rpa.db` con la siguiente estructura:
- `datetime`: Fecha y hora de ejecución
- `sender`: Remitente del correo
- `subject`: Asunto del correo
- `message_content`: Contenido del mensaje
- `extracted_url`: URL extraída
- `status`: Estado del proceso
- `detailed_error`: Error detallado (si aplica)
- `final_result`: Resultado final
- `process_id`: ID único del proceso

## ⚙️ Configuración

### Intervalo de ejecución
Por defecto, el sistema se ejecuta cada 10 minutos. Para cambiar esto, edita:
- `src/main.py` (línea 258)

Cambia `time.sleep(600)` por el número de segundos deseado.

### Modo headless
Para servidores VPS, se recomienda usar `MODO_HEADLESS=true` en el archivo `.env`.

## 🔧 Solución de problemas

### Error de Chrome/Chromium
```bash
# Instalar dependencias adicionales
sudo apt install -y xvfb
```

### Error de permisos
```bash
# Verificar permisos del directorio
chmod 755 src/
```

### Error de base de datos
```bash
# Verificar permisos de escritura
chmod 755 .
```

## 📝 Notas importantes

1. **Seguridad**: Nunca subas el archivo `.env` a Git
2. **Credenciales**: Usa contraseñas de aplicación para Gmail
3. **Recursos**: El sistema consume memoria y CPU, monitorea el uso
4. **Logs**: Revisa regularmente los logs para detectar errores
5. **Backup**: Haz respaldo regular de la base de datos

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. 