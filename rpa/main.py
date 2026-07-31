#!/usr/bin/env python3
"""
Sistema de Automatización RPA - Archivo Principal
Orquesta todo el flujo de lectura de correos, extracción de links y automatización web.
"""

import os
import logging
import logging.handlers
import time
import shutil
from datetime import datetime, date
from dotenv import load_dotenv
from imap_tools.mailbox import MailBox
from imap_tools.query import AND

# Importar módulos del sistema
from email_reader import EmailReader
from driver_web import WebDriver
from database import Database

# Configurar logging
#
# El timer corre cada 30 segundos, asi que un unico archivo crece sin freno
# (llego a 472 MB / 5.9 millones de lineas). Con rotacion diaria, cada
# medianoche el log del dia pasa a rpa_system.log.AAAA-MM-DD y se conserva
# un mes: backupCount=30 borra automaticamente el archivo mas viejo, que es
# justo lo que sobra pasados los 30 dias.
#
# La rotacion la hace el propio logging al escribir la primera linea despues
# de medianoche (un rename mas un unlink, milisegundos). Si llegara a fallar,
# logging captura el error y sigue: no puede detener la ejecucion ni el timer.
#
# Ruta absoluta a partir de este archivo para no depender del directorio de
# trabajo (systemd usa WorkingDirectory=/root/automatizacion, pero una
# ejecucion manual desde otra carpeta escribiria el log en otro sitio).
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rpa_system.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.TimedRotatingFileHandler(
            LOG_PATH, when='midnight', backupCount=30, encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_selenium_cache():
    """
    Limpia el cache de Selenium para liberar espacio en disco.
    """
    try:
        selenium_cache = os.path.expanduser("~/.cache/selenium")
        if os.path.exists(selenium_cache):
            # Limpiar directorios de Chrome
            chrome_dir = os.path.join(selenium_cache, "chrome", "linux64")
            chromedriver_dir = os.path.join(selenium_cache, "chromedriver", "linux64")
            
            if os.path.exists(chrome_dir):
                for item in os.listdir(chrome_dir):
                    item_path = os.path.join(chrome_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        logger.info(f"Directorio de Chrome eliminado: {item}")
            
            if os.path.exists(chromedriver_dir):
                for item in os.listdir(chromedriver_dir):
                    item_path = os.path.join(chromedriver_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        logger.info(f"Directorio de ChromeDriver eliminado: {item}")
            
            logger.info("Cache de Selenium limpiado exitosamente")
        else:
            logger.info("No se encontró cache de Selenium para limpiar")
            
    except Exception as e:
        logger.error(f"Error limpiando cache de Selenium: {str(e)}")

def should_cleanup_selenium(flag_path: str) -> bool:
    """
    Determina si debe ejecutarse la limpieza de Selenium (cada 7 días).
    """
    today = date.today().isoformat()
    if not os.path.exists(flag_path):
        return True
    
    with open(flag_path, 'r') as f:
        last_run = f.read().strip()
    
    # Calcular días desde la última limpieza
    try:
        last_date = date.fromisoformat(last_run)
        days_diff = (date.today() - last_date).days
        return days_diff >= 7
    except:
        return True

def update_selenium_cleanup_flag(flag_path: str):
    """
    Actualiza el archivo de marca de tiempo de limpieza de Selenium.
    """
    today = date.today().isoformat()
    with open(flag_path, 'w') as f:
        f.write(today)

def process_emails():
    """
    Función que procesa los correos electrónicos.
    """
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Inicializar componentes
        db = Database()
        email_reader = EmailReader()
        web_driver = WebDriver()
        
        # Leer solo los correos no leídos del remitente filtrado para procesar URLs
        logger.info("Leyendo correos de Netflix...")
        
        # Obtener todos los correos no leídos
        all_unread_emails = email_reader.get_unread_emails()
        
        filtered_emails = [email for email in all_unread_emails if email.from_.lower() == email_reader.sender_filter.lower()]
        
        # Filtrar solo correos que no sean solicitudes de reporte
        emails_to_process = [email for email in filtered_emails if not ("REPORTE" in email.subject.upper() or "REPORTE" in email.text.upper())]
        
        if not emails_to_process:
            logger.info("No hay correos de Netflix para procesar")
            return
        logger.info(f"Hay {len(emails_to_process)} correos de Netflix para procesar")
        
        # Procesar cada correo
        for email in emails_to_process:
            try:
                logger.info(f"Procesando correo: {email.subject}")
                
                # Extraer link del correo
                logger.info("Extrayendo URL...")
                link = email_reader.extract_link_from_email(email)
                
                if link:
                    logger.info(f"URL extraída: {link}")
                    logger.info("Abriendo en navegador...")
                    
                    # Abrir link y hacer clic en botón
                    success = web_driver.click_button_on_page(link)
                    
                    if success:
                        logger.info("Haciendo click...")
                        logger.info("Click exitoso")
                        
                        db.insert_success_record(
                            sender=email.from_,
                            subject=email.subject,
                            link=link,
                            status="SUCCESS",
                            observations="Procesado correctamente"
                        )
                        
                        # Eliminar correo automáticamente si está habilitado
                        if email_reader.should_auto_delete_emails():
                            if email_reader.delete_email(email):
                                logger.info("Correo eliminado")
                            else:
                                logger.warning("Error al eliminar correo")
                        else:
                            logger.info("Correo mantenido (eliminación deshabilitada)")
                            
                    else:
                        logger.error("Click fallido")
                        db.insert_failed_record(
                            sender=email.from_,
                            subject=email.subject,
                            link=link,
                            status="FAILED",
                            observations="Error al hacer clic en botón"
                        )
                        
                else:
                    logger.info("No se encontró URL válida")
                    
                    # Registrar fallo por falta de URL
                    db.insert_failed_record(
                        sender=email.from_,
                        subject=email.subject,
                        link="",
                        status="NO_URL",
                        observations="Correo sin URL válida de Netflix"
                    )
                    
                    # Eliminar correo sin URL automáticamente
                    if email_reader.should_auto_delete_emails():
                        if email_reader.delete_email(email):
                            logger.info("Correo sin URL eliminado")
                        else:
                            logger.warning("Error al eliminar correo sin URL")
                    else:
                        logger.info("Correo sin URL mantenido (eliminación deshabilitada)")
                    
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                db.insert_failed_record(
                    sender=email.from_,
                    subject=email.subject,
                    link="",
                    status="ERROR",
                    observations=f"Error: {str(e)}",
                    error_details=str(e)
                )
                
                # Eliminar correo con error automáticamente
                if email_reader.should_auto_delete_emails():
                    if email_reader.delete_email(email):
                        logger.info("Correo con error eliminado")
                    else:
                        logger.warning("Error al eliminar correo con error")
                else:
                    logger.info("Correo con error mantenido (eliminación deshabilitada)")
        
        logger.info("Proceso completado")
        
    except Exception as e:
        logger.error(f"Error general en el sistema: {str(e)}")

def should_run_cleanup(flag_path: str) -> bool:
    """
    Determina si debe ejecutarse la limpieza de la base de datos (una vez al día).
    """
    today = date.today().isoformat()
    if not os.path.exists(flag_path):
        return True
    with open(flag_path, 'r') as f:
        last_run = f.read().strip()
    return last_run != today

def update_cleanup_flag(flag_path: str):
    """
    Actualiza el archivo de marca de tiempo de limpieza.
    """
    today = date.today().isoformat()
    with open(flag_path, 'w') as f:
        f.write(today)

def main():
    """
    Función principal que ejecuta el sistema RPA una sola vez (sin bucle infinito).
    """
    logger.info("Iniciando sistema RPA en modo ciclo único...")
    cleanup_flag = "db_cleanup.flag"
    selenium_cleanup_flag = "selenium_cleanup.flag"
    db = Database()
    
    # Limpieza automática de base de datos una vez al día
    if should_run_cleanup(cleanup_flag):
        eliminados = db.delete_old_records(days=30)
        logger.info(f"Limpieza diaria: {eliminados} registros eliminados por antigüedad.")
        update_cleanup_flag(cleanup_flag)
    
    # Limpieza automática de Selenium cada 7 días
    if should_cleanup_selenium(selenium_cleanup_flag):
        cleanup_selenium_cache()
        update_selenium_cleanup_flag(selenium_cleanup_flag)
    

    
    process_emails()

if __name__ == "__main__":
    main() 