"""
Lee correos desde un servidor IMAP, extrae enlaces y registra los resultados en la base de datos.
"""
from sub.database import save_record
from datetime import datetime
from imap_tools.mailbox import MailBox
from imap_tools.query import AND
from dotenv import load_dotenv
import os
import re
from bs4 import BeautifulSoup, Tag

load_dotenv()

USUARIO = os.getenv("USUARIO_CORREO")
CLAVE = os.getenv("CLAVE_CORREO")
IMAP_SERVIDOR = os.getenv("IMAP_SERVIDOR")
FILTRO_REMITENTE = os.getenv("FILTRO_REMITENTE")
TEXTO_BOTON_URL = os.getenv("TEXTO_BOTON_URL")
PATRON_URL = os.getenv("PATRON_URL")

def validate_credentials():
    """Valida que todas las credenciales requeridas estén configuradas."""
    if not USUARIO or not CLAVE or not IMAP_SERVIDOR:
        raise ValueError("Faltan credenciales en el archivo .env. Verifica USUARIO_CORREO, CLAVE_CORREO e IMAP_SERVIDOR")
    return True

def extract_links(text):
    """Extrae todas las URLs que coincidan con el patrón especificado, o todas las URLs si no se establece un patrón."""
    if PATRON_URL:
        patron = re.escape(PATRON_URL) + r"[\w\-\?&=/%#\.]+"
        links = re.findall(patron, text)
        return links
    patron = r'https?://[^\s]+'
    return re.findall(patron, text)

def read_unread_filtered_emails():
    """Lee correos no leídos, filtra por remitente, extrae enlaces y registra los resultados."""
    try:
        validate_credentials()
        usuario = str(USUARIO)
        clave = str(CLAVE)
        servidor = str(IMAP_SERVIDOR)
        with MailBox(servidor).login(usuario, clave, initial_folder="INBOX") as mailbox:
            mensajes = mailbox.fetch(criteria=AND(seen=False), limit=10, reverse=True)
            for i, mensaje in enumerate(mensajes, start=1):
                if FILTRO_REMITENTE and FILTRO_REMITENTE.lower() in mensaje.from_.lower():
                    print(f"\n--- CORREO #{i} ---")
                    print("De:", mensaje.from_)
                    print("Asunto:", mensaje.subject)
                    print("Fecha:", mensaje.date)
                    print("Contenido (primeros 300 caracteres):")
                    print(mensaje.text[:300])
                    links = extract_links(mensaje.text)
                    if links:
                        print("Links encontrados:")
                        for link in links:
                            print(" ➡️", link)
                    else:
                        print("Sin links en este correo.")
                    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    remitente = mensaje.from_
                    asunto = mensaje.subject
                    link_todos = ", ".join(links)
                    link_extraido = links[0] if links else ""
                    status = "Éxito"
                    observaciones = "Procesado correctamente"
                    guardar_registro(
                        fecha_hora,
                        remitente,
                        asunto,
                        link_extraido,
                        link_todos,
                        status,
                        observaciones
                    )
    except Exception as e:
        print(" Error al leer correos:", e)

if __name__ == "__main__":
    read_unread_filtered_emails()
