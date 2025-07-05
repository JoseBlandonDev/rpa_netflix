"""
Script principal del RPA: Orquesta la lectura de correos, extracción de enlaces, automatización web y registro en la base de datos.
"""
from sub.email_reader import validate_credentials, extract_links
from sub.driver_web import WebAutomator
from sub.database import save_record, get_next_process_id
from datetime import datetime
from imap_tools.mailbox import MailBox
from imap_tools.query import AND
from dotenv import load_dotenv
import os
import time
import requests

load_dotenv()

USUARIO = os.getenv("USUARIO_CORREO")
CLAVE = os.getenv("CLAVE_CORREO")
IMAP_SERVIDOR = os.getenv("IMAP_SERVIDOR")
FILTRO_REMITENTE = os.getenv("FILTRO_REMITENTE")

SELECTOR_BOTON = os.getenv("SELECTOR_BOTON", "//button | //a[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Iniciar sesión') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]")
TIPO_SELECTOR = os.getenv("TIPO_SELECTOR", "xpath")
MODO_HEADLESS = os.getenv("MODO_HEADLESS", "true").lower() == "true"

class FullRPA:
    """
    Sistema de automatización completo:
    1. Lee correos filtrados
    2. Extrae enlaces
    3. Abre enlaces con Selenium
    4. Hace clic en botones
    5. Registra todo en la base de datos
    """
    
    def __init__(self, headless=True, debug=True):
        """
        Inicializa el sistema RPA.
        Args:
            headless (bool): Modo headless para Selenium
            debug (bool): Mostrar información detallada
        """
        self.headless = headless
        self.debug = debug
        self.automator = None
        self.total_processed = 0
        self.total_success = 0
        self.total_errors = 0
    
    def log(self, mensaje):
        """Muestra un mensaje solo si debug está activado."""
        if self.debug:
            print(mensaje)
    
    def process_emails_automatically(self):
        """
        Función principal que ejecuta todo el proceso RPA.
        """
        self.log("STARTING FULL AUTOMATION PROCESS")
        self.log("=" * 60)
        
        try:
            validate_credentials()
            self.log("Credentials validated")
            self.automator = WebAutomator(headless=self.headless)
            self.log(f"Web automator initialized (headless={self.headless})")
            self._read_and_process_emails()
        except Exception as e:
            self.log(f"General error in process: {e}")
            self._register_general_error(str(e))
        finally:
            if self.automator:
                self.automator.close_browser()
            self._show_summary()
    
    def _read_and_process_emails(self):
        """Lee correos y procesa cada uno con Selenium."""
        self.log("\nREADING EMAILS...")
        usuario = str(USUARIO)
        clave = str(CLAVE)
        servidor = str(IMAP_SERVIDOR)
        with MailBox(servidor).login(usuario, clave, initial_folder="INBOX") as mailbox:
            mensajes = mailbox.fetch(criteria=AND(seen=False), limit=10, reverse=True)
            for i, mensaje in enumerate(mensajes, start=1):
                if FILTRO_REMITENTE and FILTRO_REMITENTE.lower() in mensaje.from_.lower():
                    self.log(f"\nPROCESSING EMAIL #{i}")
                    self.log(f"   From: {mensaje.from_}")
                    self.log(f"   Subject: {mensaje.subject}")
                    self._process_single_email(mensaje, i)
    
    def _process_single_email(self, mensaje, numero):
        """Procesa un correo individual con Selenium."""
        process_id = get_next_process_id()
        self.log(f"   Process ID: {process_id}")
        try:
            message_content = mensaje.text or mensaje.html or "No content"
            self.log(f"   Extracted content: {len(message_content)} characters")
            links = extract_links(message_content)
            self.log(f"   Links found: {len(links)}")
            if not links:
                self._register_full_result(
                    mensaje, message_content, "", "No links", 
                    "No URLs found in the email", 
                    "Process completed without URLs", process_id
                )
                return
            extracted_url = links[0]
            self.log(f"   Processing URL: {extracted_url}")
            if not self._validate_url(extracted_url):
                self._register_full_result(
                    mensaje, message_content, extracted_url, "Invalid URL",
                    "The URL is not accessible or is malformed",
                    "URL validation error", process_id
                )
                self.total_errors += 1
                return
            selenium_result = self._run_web_automation(extracted_url)
            if selenium_result["success"]:
                self.total_success += 1
                status = "Success"
                final_result = "Button clicked successfully"
            else:
                self.total_errors += 1
                status = "Error"
                final_result = "Web automation failed"
            self._register_full_result(
                mensaje, message_content, extracted_url, status,
                selenium_result["observations"], final_result, process_id
            )
            self.total_processed += 1
        except Exception as e:
            self.log(f"Error processing email #{numero}: {e}")
            self._register_full_result(
                mensaje, message_content if 'message_content' in locals() else "Error extracting content",
                extracted_url if 'extracted_url' in locals() else "", "Error",
                f"Error processing email: {e}", "Processing failed", process_id
            )
            self.total_errors += 1
    
    def _validate_url(self, url):
        """Verifica si la URL es accesible."""
        try:
            self.log(f"Validating URL: {url}")
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                self.log("URL valid and accessible")
                return True
            elif response.status_code == 404:
                self.log("Error 404: Page not found")
                return False
            elif response.status_code in [403, 401]:
                self.log("Access error: Page blocked or requires authentication")
                return False
            else:
                self.log(f"Status code: {response.status_code}")
                return True
        except requests.exceptions.ConnectionError:
            self.log("Connection error: Cannot connect to server")
            return False
        except requests.exceptions.Timeout:
            self.log("Timeout: URL took too long to respond")
            return False
        except Exception as e:
            self.log(f"Error validating URL: {e}")
            return False
    
    def _run_web_automation(self, url):
        """Ejecuta la automatización web en un enlace específico, probando múltiples selectores de elementos clickeables."""
        try:
            if not self.automator.open_link(url):
                return {"success": False, "observations": "Could not open link in browser"}
            time.sleep(3)
            title = self.automator.get_page_title()
            self.log(f"Page title: {title}")
            selectors_to_test = [
                "//button[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Iniciar sesión') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]",
                "//a[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Iniciar sesión') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]",
                "//button",
                "//a[contains(@href, '#') or contains(@href, 'javascript')]",
                "//input[@type='submit']",
                "//input[@type='button']"
            ]
            for i, selector in enumerate(selectors_to_test, 1):
                self.log(f"Testing selector {i}: {selector}")
                if self.automator.click_button(selector, "xpath", f"element {i}"):
                    return {"success": True, "observations": f"Click successful with selector {i}"}
                else:
                    result = self.automator.get_last_click_result()
                    self.log(f"Selector {i} failed: {result['observations']}")
            return {"success": False, "observations": "No clickable element found on the page"}
        except Exception as e:
            return {"success": False, "observations": f"Web automation error: {e}"}

    def _register_full_result(self, mensaje, contenido_mensaje, url_extraida, status, error_detallado, resultado_final, id_proceso):
        """Registra el resultado completo en la base de datos."""
        try:
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            remitente = mensaje.from_
            asunto = mensaje.subject
            contenido_truncado = contenido_mensaje[:5000] + "..." if len(contenido_mensaje) > 5000 else contenido_mensaje
            save_record(
                fecha_hora, remitente, asunto, contenido_truncado,
                url_extraida, status, error_detallado, resultado_final, id_proceso
            )
            self.log(f"Record saved: {status} - ID: {id_proceso}")
        except Exception as e:
            self.log(f"Error saving to DB: {e}")

    def _register_general_error(self, error_msg):
        """Registra errores generales del sistema en la base de datos."""
        try:
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            process_id = get_next_process_id()
            save_record(
                fecha_hora, "SYSTEM", "ERROR_GENERAL", 
                "System error", "", "Error", f"System error: {error_msg}",
                "General failure", process_id
            )
        except:
            pass

    def _show_summary(self):
        """Muestra un resumen del proceso RPA."""
        self.log("FULL AUTOMATION PROCESS SUMMARY")
        self.log("=" * 40)
        self.log(f"Emails processed: {self.total_processed}")
        self.log(f"Successes: {self.total_success}")
        self.log(f"Errors: {self.total_errors}")
        if self.total_processed > 0:
            success_rate = (self.total_success / self.total_processed) * 100
            self.log(f"Success rate: {success_rate:.1f}%")
        self.log("FULL AUTOMATION PROCESS COMPLETED")

def run_full_rpa(headless=True, debug=True):
    """
    Ejecuta el proceso RPA completo.
    Args:
        headless (bool): Ejecutar en modo headless
        debug (bool): Mostrar información detallada
    """
    rpa = FullRPA(headless=headless, debug=debug)
    rpa.process_emails_automatically()

if __name__ == "__main__":
    print("FULL RPA SYSTEM")
    print("=" * 30)
    print("This system will automatically process emails")
    print("and execute web actions with Selenium.")
    print()
    headless = True
    print(f"Executing in headless mode...")
    print("Press Ctrl+C to cancel if necessary.\n")
    try:
        while True:
            run_full_rpa(headless=headless, debug=True)
            print("Waiting 10 minutes for the next execution...")
            time.sleep(600)
    except KeyboardInterrupt:
        print("\nExecution stopped by user.") 