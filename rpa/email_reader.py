#!/usr/bin/env python3
"""
Módulo para lectura de correos electrónicos
Contiene funciones para conectar a IMAP, leer correos no leídos y extraer links.
"""

import os
import re
import logging
from typing import List, Optional
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
        self.link_pattern = os.getenv('LINK_PATTERN', r'https?://[^\s<>"]+')
        
        if not self.email or not self.password:
            raise ValueError("EMAIL_ADDRESS y EMAIL_PASSWORD deben estar configurados en .env")
    
    def get_unread_emails(self):
        """
        Obtiene los correos no leídos de la bandeja de entrada que coincidan con el filtro de remitente.
        Returns:
            list: Lista de objetos Email
        """
        try:
            with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                # Buscar solo correos no leídos y del remitente filtrado
                emails = [email for email in mailbox.fetch('(UNSEEN)', mark_seen=True, bulk=True)
                          if email.from_.lower() == self.sender_filter.lower()]
                logger.info(f"get_unread_emails: encontrados {len(emails)} correos no leídos del remitente filtrado.")
                for email in emails:
                    logger.info(f"Correo no leído: De: {email.from_} | Asunto: {email.subject}")
                return emails
        except Exception as e:
            logger.error(f"Error obteniendo correos no leídos: {str(e)}")
            return []
    
    def extract_link_from_email(self, email) -> Optional[str]:
        """
        Extrae el link del botón rojo de Netflix decodificando el HTML y usando BeautifulSoup.
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
                    if '/account/update-primary-location' in a['href']:
                        logger.info(f"Link correcto encontrado en HTML: {a['href']}")
                        return a['href']
            # 2. Buscar en el texto plano como respaldo
            if email.text:
                text = email.text
                if '=3D' in text:
                    text = quopri.decodestring(text).decode('utf-8', errors='ignore')
                links = re.findall(self.link_pattern, text)
                for link in links:
                    if '/account/update-primary-location' in link:
                        logger.info(f"Link correcto encontrado en texto: {link}")
                        return link
            logger.warning(f"No se encontró link válido en el correo: {email.subject}")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo link del correo: {str(e)}")
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
            with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                mailbox.seen(email.uid, True)
                logger.info(f"Correo marcado como leído: {email.subject}")
                return True
                
        except Exception as e:
            logger.error(f"Error marcando correo como leído: {str(e)}")
            return False 

    def process_report_requests(self, emails):
        """
        Procesa solicitudes de reporte y responde con el archivo Excel si corresponde.
        Args:
            emails: lista de emails no leídos
        """
        try:
            db = Database()
            with MailBox(self.imap_server).login(self.email, self.password) as mailbox:
                for email in emails:
                    logger.info(f"Revisando correo de {email.from_} con asunto: {email.subject}")
                    
                    # Verificar si el correo ya fue procesado anteriormente
                    if db.is_email_processed(str(email.uid)):
                        logger.info(f"Correo UID {email.uid} ya fue procesado anteriormente, saltando...")
                        continue
                    
                    if ("REPORTE" in email.subject.upper() or "REPORTE" in email.text.upper()):
                        logger.info(f"Palabra clave 'REPORTE' detectada en el correo de {email.from_}")
                        
                        # Marcar como procesado ANTES de enviar el reporte
                        db.mark_email_processed(str(email.uid), email.from_, email.subject, 'reporte')
                        
                        excel_path = db.export_to_excel()
                        if excel_path:
                            send_report_email(email.from_, excel_path)
                            logger.info(f"Reporte enviado a {email.from_}")
                        else:
                            logger.error("No se pudo generar el archivo Excel para el reporte.")
                        
                        # Marcar el correo como leído usando el flag estándar IMAP
                        try:
                            mailbox.flag(email.uid, '\\Seen', True)
                            logger.info(f"Correo marcado como leído (UID: {email.uid}): {email.subject}")
                        except Exception as e:
                            logger.error(f"No se pudo marcar como leído: {str(e)}")
                    else:
                        logger.info(f"Correo de {email.from_} no contiene la palabra clave 'REPORTE'.")
        except Exception as e:
            logger.error(f"Error en process_report_requests: {str(e)}") 