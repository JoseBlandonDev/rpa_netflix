"""
Utilidades de automatización web usando Selenium para tareas RPA: configuración del navegador, navegación y clic en botones.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

class WebAutomator:
    """
    Clase para manejar la automatización web con Selenium, optimizada para entornos Linux y servidores.
    """
    
    def __init__(self, headless=True):
        """
        Inicializa el automatizador web.
        Args:
            headless (bool): Si es True, ejecuta el navegador en modo headless (ideal para VPS)
        """
        self.driver = None
        self.headless = headless
        self.wait_timeout = 10
        self.resultado_ultimo_clic = {"exito": False, "observaciones": ""}
    
    def configure_browser(self):
        """
        Configura y abre el navegador Chrome con opciones para Linux.
        Returns:
            bool: True si se configuró correctamente, False en caso contrario
        """
        try:
            print("Configurando navegador Chrome...")
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
                print("   Modo headless activado")
            else:
                print("   Modo con ventana visible")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            print("   Configurando Chromium/ChromeDriver...")
            try:
                servicio = Service(ChromeDriverManager().install())
                chrome_options.binary_location = "/usr/bin/chromium-browser"
                self.driver = webdriver.Chrome(service=servicio, options=chrome_options)
            except Exception as e:
                print(f"   Instalación automática falló, intentando configuración manual...")
                self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.wait_timeout)
            print("Navegador configurado correctamente")
            return True
        except Exception as e:
            print(f"Error al configurar navegador: {e}")
            self.resultado_ultimo_clic = {"exito": False, "observaciones": f"Error configuración: {e}"}
            return False
    
    def open_link(self, url):
        """
        Abre un enlace específico en el navegador.
        Args:
            url (str): La URL a abrir
        Returns:
            bool: True si se abrió correctamente, False en caso contrario
        """
        try:
            if not self.driver:
                if not self.configure_browser():
                    return False
            print(f"Abriendo link: {url}")
            self.driver.get(url)
            time.sleep(3)
            titulo = self.driver.title[:50] + "..." if len(self.driver.title) > 50 else self.driver.title
            print(f"Página cargada: '{titulo}'")
            return True
        except Exception as e:
            print(f"Error al abrir link: {e}")
            self.resultado_ultimo_clic = {"exito": False, "observaciones": f"Error al abrir link: {e}"}
            return False
    
    def click_button(self, selector, selector_type="xpath", description="button"):
        """
        Hace clic en un botón específico de la página.
        Args:
            selector (str): Selector del botón (XPath, CSS, ID, etc.)
            selector_type (str): Tipo de selector ("xpath", "css", "id", "class", "tag")
            description (str): Descripción para los logs
        Returns:
            bool: True si el clic fue exitoso, False en caso contrario
        """
        try:
            if not self.driver:
                print("No hay navegador abierto")
                self.resultado_ultimo_clic = {"exito": False, "observaciones": "No hay navegador abierto"}
                return False
            tipos_selector = {
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME
            }
            if selector_type not in tipos_selector:
                print(f"Tipo de selector no válido: {selector_type}")
                self.resultado_ultimo_clic = {"exito": False, "observaciones": f"Selector inválido: {selector_type}"}
                return False
            print(f"Buscando {description}: {selector}")
            wait = WebDriverWait(self.driver, self.wait_timeout)
            elemento = wait.until(
                EC.element_to_be_clickable((tipos_selector[selector_type], selector))
            )
            print(f"Haciendo clic en {description}")
            elemento.click()
            time.sleep(2)
            print(f"Clic en {description} realizado correctamente")
            self.resultado_ultimo_clic = {"exito": True, "observaciones": f"Clic exitoso en {description}"}
            return True
        except Exception as e:
            print(f"Error al hacer clic en {description}: {e}")
            self.resultado_ultimo_clic = {"exito": False, "observaciones": f"Error en clic: {e}"}
            return False
    
    def get_page_title(self):
        """
        Obtiene el título de la página actual.
        Returns:
            str: El título de la página o None si hay error
        """
        try:
            if self.driver:
                return self.driver.title
            return None
        except Exception as e:
            print(f"Error al obtener título: {e}")
            return None
    
    def get_current_url(self):
        """
        Obtiene la URL actual de la página.
        Returns:
            str: La URL actual o None si hay error
        """
        try:
            if self.driver:
                return self.driver.current_url
            return None
        except Exception as e:
            print(f"Error al obtener URL: {e}")
            return None
    
    def get_last_click_result(self):
        """
        Obtiene el resultado del último intento de clic.
        Returns:
            dict: Resultado del último clic
        """
        return self.resultado_ultimo_clic
    
    def close_browser(self):
        """
        Cierra el navegador si está abierto.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        # No requiere docstring, destructor simple
        self.close_browser()

def simple_click_test(url, button_selector, selector_type="xpath", headless=True):
    """
    Función de prueba simple para abrir una URL y hacer clic en un botón.
    """
    auto = WebAutomator(headless=headless)
    if auto.open_link(url):
        auto.click_button(button_selector, selector_type)
    auto.close_browser() 