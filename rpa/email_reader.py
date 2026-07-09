#!/usr/bin/env python3
"""
Módulo para lectura de correos electrónicos
Contiene funciones para conectar a IMAP, leer correos no leídos y extraer links.
"""

import os
import re
import logging
import socket
from typing import List, Optional
from datetime import datetime, timedelta
from imap_tools.mailbox import MailBox
from imap_tools.query import AND
from dotenv import load_dotenv
import quopri
from bs4 import BeautifulSoup
from notifier import send_report_email
from database import Database

logger = logging.getLogger(__name__)

class EmailReader:
    """
    Clase para manejar la lectura de correos electrónicos via IMAP.
    """
    
    def __init__(self):
        """
        Inicializa el lector de correos con configuración desde variables de entorno.
        """
        load_dotenv()
        
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.sender_filter = os.getenv('SENDER_FILTER', 'netflix.com')
        self.link_pattern = os.getenv('LINK_PATTERN', 'https://www.netflix.com/account/update-primary-location')
        self.imap_timeout = int(os.getenv('IMAP_TIMEOUT', '30'))
        
        if not self.email or not self.password:
            raise ValueError("EMAIL_ADDRESS y EMAIL_PASSWORD deben estar configurados en .env")
    
    def get_unread_emails(self):
        """
        Obtiene los correos no leídos de la bandeja de entrada que coincidan con el filtro de remitente
        y que hayan sido recibidos en los últimos 5 minutos.
        Returns:
            list: Lista de objetos Email
        """
        try:
            # Configurar timeout a nivel de socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.imap_timeout)
            
            try:
                with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                    # Calcular la fecha/hora de hace 5 minutos
                    cutoff_time = datetime.now() - timedelta(minutes=5)
                    
                    # Obtener todos los correos no leídos
                    # Luego filtrar por fecha y remitente en Python para mayor confiabilidad
                    emails = []
                    for email in mailbox.fetch('(UNSEEN)', mark_seen=True, bulk=True):
                        # Filtrar por remitente
                        if email.from_.lower() == self.sender_filter.lower():
                            # Verificar que el correo sea de los últimos 5 minutos
                            email_date = email.date
                            if email_date and isinstance(email_date, datetime):
                                # Convertir email_date a naive datetime si tiene timezone
                                # para comparar con cutoff_time (que es naive)
                                if email_date.tzinfo is not None:
                                    # Convertir a timezone local y luego a naive
                                    try:
                                        email_date_naive = email_date.astimezone().replace(tzinfo=None)
                                    except:
                                        # Si falla la conversión, usar replace directo
                                        email_date_naive = email_date.replace(tzinfo=None)
                                else:
                                    email_date_naive = email_date
                                
                                # Comparar con cutoff_time
                                if email_date_naive >= cutoff_time:
                                    emails.append(email)
                    
                    logger.info(f"Encontrados {len(emails)} correos no leídos de los últimos 5 minutos")
                    return emails
            finally:
                # Restaurar timeout original
                socket.setdefaulttimeout(old_timeout)
        except socket.timeout:
            logger.error(f"Timeout obteniendo correos (más de {self.imap_timeout} segundos)")
            return []
        except Exception as e:
            logger.error(f"Error obteniendo correos no leídos: {str(e)}")
            return []
    
    def extract_link_from_email(self, email) -> Optional[str]:
        """
        Extrae el link que coincida con el patrón configurado en LINK_PATTERN.
        """
        try:
            # 1. Buscar en el HTML (decodificando si es necesario)
            if email.html:
                html = email.html
                # Decodificar si está en quoted-printable
                if 'Content-Transfer-Encoding: quoted-printable' in str(email.headers) or '=3D' in html:
                    html = quopri.decodestring(html).decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # Verificar que coincida con el patrón configurado
                    if self.link_pattern in href:
                        logger.info(f"URL encontrada que coincide con el patrón: {href}")
                        return href
                    elif 'netflix.com/account/update-primary-location' in href:
                        logger.info(f"URL de actualización de ubicación encontrada: {href}")
                        return href
            
            # 2. Buscar en el texto plano como respaldo
            if email.text:
                text = email.text
                if '=3D' in text:
                    text = quopri.decodestring(text).decode('utf-8', errors='ignore')
                # Buscar URLs que coincidan con el patrón específico
                if self.link_pattern in text:
                    # Extraer la URL completa del patrón
                    pattern_start = text.find(self.link_pattern)
                    if pattern_start != -1:
                        # Buscar el final de la URL (espacio, salto de línea, etc.)
                        url_end = text.find(' ', pattern_start)
                        if url_end == -1:
                            url_end = text.find('\n', pattern_start)
                        if url_end == -1:
                            url_end = len(text)
                        
                        url = text[pattern_start:url_end].strip()
                        logger.info(f"URL extraída del texto que coincide con el patrón: {url}")
                        return url
            
            logger.warning("No se encontró URL que coincida con el patrón configurado")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo URL: {str(e)}")
            return None
    
    def mark_email_as_read(self, email) -> bool:
        """
        Marca un correo como leído.
        
        Args:
            email: Objeto de correo de imap-tools
            
        Returns:
            bool: True si se marcó correctamente, False en caso contrario
        """
        try:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.imap_timeout)
            try:
                with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                    mailbox.seen(email.uid, True)
                    return True
            finally:
                socket.setdefaulttimeout(old_timeout)
        except socket.timeout:
            logger.error(f"Timeout marcando como leído (más de {self.imap_timeout} segundos)")
            return False
        except Exception as e:
            logger.error(f"Error marcando como leído: {str(e)}")
            return False 

    def delete_email(self, email) -> bool:
        """
        Elimina un correo de la bandeja de entrada.
        
        Args:
            email: Objeto de correo de imap-tools
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        try:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.imap_timeout)
            try:
                with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                    # Eliminar el correo usando su UID
                    mailbox.delete(email.uid)
                    return True
            finally:
                socket.setdefaulttimeout(old_timeout)
        except socket.timeout:
            logger.error(f"Timeout eliminando correo (más de {self.imap_timeout} segundos)")
            return False
        except Exception as e:
            logger.error(f"Error eliminando correo: {str(e)}")
            return False

    def should_auto_delete_emails(self) -> bool:
        """
        Verifica si la eliminación automática de correos está habilitada.
        
        Returns:
            bool: True si está habilitada, False en caso contrario
        """
        auto_delete = os.getenv('AUTO_DELETE_EMAILS', 'false').lower()
        return auto_delete in ['true', '1', 'yes', 'on']

    def process_report_requests(self, emails):
        """
        Procesa solicitudes de reporte y responde con el archivo Excel si corresponde.
        Args:
            emails: lista de emails no leídos
        """
        try:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.imap_timeout)
            try:
                with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                    for email in emails:
                        if ("REPORTE" in email.subject.upper() or "REPORTE" in email.text.upper()):
                            db = Database()
                            excel_path = db.export_to_excel()
                            if excel_path:
                                send_report_email(email.from_, excel_path)
                                logger.info("Reporte enviado")
                                
                                # Eliminar correo automáticamente si está habilitado
                                if self.should_auto_delete_emails():
                                    if self.delete_email(email):
                                        logger.info("Correo de reporte eliminado")
                                    else:
                                        logger.warning("Error al eliminar correo de reporte")
                            else:
                                logger.error("Error generando reporte Excel")
            finally:
                socket.setdefaulttimeout(old_timeout)
        except socket.timeout:
            logger.error(f"Timeout en process_report_requests (más de {self.imap_timeout} segundos)")
        except Exception as e:
            logger.error(f"Error en process_report_requests: {str(e)}")