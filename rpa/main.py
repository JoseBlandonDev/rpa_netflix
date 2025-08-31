#!/usr/bin/env python3
"""
Sistema de Automatización RPA - Archivo Principal
Orquesta todo el flujo de lectura de correos, extracción de links y automatización web.
"""

import os
import logging
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpa_system.log'),
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
        
        # Leer todos los correos no leídos (sin marcarlos automáticamente como leídos)
        with MailBox(email_reader.imap_server).login(email_reader.email, email_reader.password) as mailbox:
            all_unread_emails = list(mailbox.fetch('(UNSEEN)', mark_seen=False, bulk=True))
        
        # Procesar solicitudes de reporte para cualquier remitente
        email_reader.process_report_requests(all_unread_emails)
        
        # Leer solo los correos no leídos del remitente filtrado para procesar URLs
        filtered_emails = [email for email in all_unread_emails if email.from_.lower() == email_reader.sender_filter.lower()]
        
        # Filtrar correos que ya fueron procesados anteriormente
        db = Database()
        unprocessed_emails = []
        for email in filtered_emails:
            if not db.is_email_processed(str(email.uid)):
                unprocessed_emails.append(email)
            else:
                logger.info(f"Correo UID {email.uid} ya fue procesado anteriormente, saltando...")
        
        emails_to_process = [email for email in unprocessed_emails if not ("REPORTE" in email.subject.upper() or "REPORTE" in email.text.upper())]
        
        if not emails_to_process:
            logger.info("No se encontraron correos no leídos para procesar")
            return
        logger.info(f"Se encontraron {len(emails_to_process)} correos no leídos para procesar")
        
        # Procesar cada correo
        for email in emails_to_process:
            try:
                # Marcar como procesado ANTES de procesar
                db.mark_email_processed(str(email.uid), email.from_, email.subject, 'url')
                
                # Extraer link del correo
                link = email_reader.extract_link_from_email(email)
                
                if link:
                    logger.info(f"Link extraído: {link}")
                    
                    # Abrir link y hacer clic en botón
                    success = web_driver.click_button_on_page(link)
                    
                    if success:
                        db.insert_success_record(
                            sender=email.from_,
                            subject=email.subject,
                            link=link,
                            status="SUCCESS",
                            observations="Procesado correctamente"
                        )
                    else:
                        db.insert_failed_record(
                            sender=email.from_,
                            subject=email.subject,
                            link=link,
                            status="FAILED",
                            observations="Error al hacer clic en botón"
                        )
                    logger.info(f"Correo procesado: {email.subject}")
                else:
                    logger.info(f"Correo sin link válido, ignorando: {email.subject}")
                    # No se registra en la base de datos, solo se marca como leído e ignora
                    
            except Exception as e:
                logger.error(f"Error procesando correo {email.subject}: {str(e)}")
                db.insert_failed_record(
                    sender=email.from_,
                    subject=email.subject,
                    link="",
                    status="ERROR",
                    observations=f"Error: {str(e)}",
                    error_details=str(e)
                )
        
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
    
    # Limpiar correos procesados antiguos
    db.cleanup_old_processed_emails(days=7)
    
    process_emails()

if __name__ == "__main__":
    main() 