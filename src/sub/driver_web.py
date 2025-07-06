"""
Web automation utilities using Selenium for RPA tasks: browser configuration, navigation and button clicking.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from sub.logger import get_logger
from sub.error_handler import handle_errors, safe_execute, WebAutomationError
import time
import os

# Get logger instance
logger = get_logger()

class WebAutomator:
    """
    Class to handle web automation with Selenium, optimized for Linux environments and servers.
    """
    
    def __init__(self, headless=True):
        """
        Initialize the web automator.
        Args:
            headless (bool): If True, runs browser in headless mode (ideal for VPS)
        """
        self.driver = None
        self.headless = headless
        self.wait_timeout = 10
        self.last_click_result = {"success": False, "observations": ""}
        
        logger.info(f"WebAutomator initialized - Headless: {headless}")
    
    @handle_errors(max_retries=2, delay=2.0)
    def configure_browser(self):
        """
        Configure and open Chrome browser with Linux options.
        Returns:
            bool: True if configured successfully, False otherwise
        """
        try:
            logger.info("Configuring Chrome browser...")
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                logger.info("   Headless mode activated")
            else:
                logger.info("   Window mode activated")
            
            # Linux-specific options
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
            
            logger.info("   Configuring Chromium/ChromeDriver...")
            
            try:
                service = Service(ChromeDriverManager().install())
                chrome_options.binary_location = "/usr/bin/chromium-browser"
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("   ChromeDriver installed automatically")
            except Exception as e:
                logger.warning(f"   Automatic installation failed, trying manual configuration...")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("   Manual ChromeDriver configuration successful")
            
            self.driver.implicitly_wait(self.wait_timeout)
            logger.info("   Browser configured successfully")
            return True
            
        except Exception as e:
            logger.error("Error configuring browser", exception=e)
            raise WebAutomationError(f"Failed to configure browser: {str(e)}")
    
    @handle_errors(max_retries=2, delay=1.0)
    def open_link(self, url):
        """
        Open a URL in the browser.
        Args:
            url (str): URL to open
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.driver:
                logger.error("No browser open")
                return False
            
            logger.info(f"Opening URL: {url}")
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            current_url = self.driver.current_url
            logger.info(f"Successfully opened URL. Current URL: {current_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening URL: {url}", exception=e)
            return False
    
    def get_page_title(self):
        """
        Get the current page title.
        Returns:
            str: Page title or empty string if error
        """
        try:
            if not self.driver:
                return ""
            
            title = self.driver.title
            logger.debug(f"Page title: {title}")
            return title
            
        except Exception as e:
            logger.error("Error getting page title", exception=e)
            return ""
    
    @handle_errors(max_retries=2, delay=1.0)
    def click_button(self, selector, selector_type="xpath", description="button"):
        """
        Click a specific button on the page.
        Args:
            selector (str): Button selector (XPath, CSS, ID, etc.)
            selector_type (str): Selector type ("xpath", "css", "id", "class", "tag")
            description (str): Description for logs
        Returns:
            bool: True if click was successful, False otherwise
        """
        try:
            if not self.driver:
                logger.error("No browser open")
                self.last_click_result = {"success": False, "observations": "No browser open"}
                return False
            
            selector_types = {
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME
            }
            
            if selector_type not in selector_types:
                logger.error(f"Invalid selector type: {selector_type}")
                self.last_click_result = {"success": False, "observations": f"Invalid selector: {selector_type}"}
                return False
            
            logger.info(f"Looking for {description}: {selector}")
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            element = wait.until(
                EC.element_to_be_clickable((selector_types[selector_type], selector))
            )
            
            logger.info(f"Clicking {description}")
            element.click()
            time.sleep(2)
            
            logger.info(f"Click on {description} successful")
            self.last_click_result = {"success": True, "observations": f"Click successful on {description}"}
            return True
            
        except Exception as e:
            logger.error(f"Error clicking {description}: {str(e)}", exception=e)
            self.last_click_result = {"success": False, "observations": f"Click error: {str(e)}"}
            return False
    
    def get_last_click_result(self):
        """
        Get the result of the last click operation.
        Returns:
            dict: Result with 'success' and 'observations' keys
        """
        return self.last_click_result
    
    def close_browser(self):
        """Close the browser and clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error("Error closing browser", exception=e)
    
    def take_screenshot(self, filename="screenshot.png"):
        """
        Take a screenshot of the current page.
        Args:
            filename (str): Screenshot filename
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.driver:
                logger.error("No browser open for screenshot")
                return False
            
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
            
        except Exception as e:
            logger.error("Error taking screenshot", exception=e)
            return False
    
    def get_page_source(self):
        """
        Get the current page source.
        Returns:
            str: Page source or empty string if error
        """
        try:
            if not self.driver:
                return ""
            
            source = self.driver.page_source
            logger.debug(f"Page source length: {len(source)} characters")
            return source
            
        except Exception as e:
            logger.error("Error getting page source", exception=e)
            return ""
    
    def wait_for_element(self, selector, selector_type="xpath", timeout=10):
        """
        Wait for an element to be present on the page.
        Args:
            selector (str): Element selector
            selector_type (str): Selector type
            timeout (int): Timeout in seconds
        Returns:
            bool: True if element found, False otherwise
        """
        try:
            if not self.driver:
                return False
            
            selector_types = {
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME
            }
            
            if selector_type not in selector_types:
                logger.error(f"Invalid selector type: {selector_type}")
                return False
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((selector_types[selector_type], selector))
            )
            
            logger.debug(f"Element found: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Error waiting for element: {selector}", exception=e)
            return False

if __name__ == "__main__":
    logger.info("Testing WebAutomator module...")
    
    try:
        automator = WebAutomator(headless=True)
        
        if automator.configure_browser():
            logger.info("Browser configured successfully")
            
            # Test opening a simple page
            success = automator.open_link("https://www.google.com")
            if success:
                title = automator.get_page_title()
                logger.info(f"Successfully opened Google. Title: {title}")
            
            automator.close_browser()
            logger.info("WebAutomator test completed successfully")
        else:
            logger.error("Failed to configure browser")
            
    except Exception as e:
        logger.error("WebAutomator test failed", exception=e) 