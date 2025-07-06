"""
Main RPA script: Orchestrates email reading, link extraction, web automation and database recording.
"""
import requests
import time
from dotenv import load_dotenv
import os
from sub.email_reader import validate_credentials, extract_links
from sub.driver_web import WebAutomator
from sub.database import save_record, get_next_process_id
from sub.logger import get_logger
from sub.error_handler import (
    handle_errors, safe_execute, ErrorRecovery, 
    log_error_context, create_error_report,
    EmailConnectionError, WebAutomationError, DatabaseError
)
from datetime import datetime
from imap_tools.mailbox import MailBox
from imap_tools.query import AND

load_dotenv()

# Get logger instance
logger = get_logger()

# Environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SENDER_FILTER = os.getenv("SENDER_FILTER")
BUTTON_SELECTOR = os.getenv("BUTTON_SELECTOR", "//button | //a[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]")
SELECTOR_TYPE = os.getenv("SELECTOR_TYPE", "xpath")
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

class FullRPA:
    """
    Complete automation system:
    1. Reads filtered emails
    2. Extracts links
    3. Opens links with Selenium
    4. Clicks buttons
    5. Records everything in database
    """
    
    def __init__(self, headless=True, debug=True):
        """
        Initialize the RPA system.
        Args:
            headless (bool): Headless mode for Selenium
            debug (bool): Show detailed information
        """
        self.headless = headless
        self.debug = debug
        self.automator = None
        self.total_processed = 0
        self.total_success = 0
        self.total_errors = 0
        self.error_details = []
        self.start_time = time.time()
        
        logger.info(f"RPA system initialized - Headless: {headless}, Debug: {debug}")
    
    def log(self, message):
        """Log a message only if debug is enabled."""
        if self.debug:
            logger.info(message)
    
    @handle_errors(max_retries=3, delay=2.0)
    def process_emails_automatically(self):
        """
        Main function that executes the complete RPA process.
        """
        logger.info("STARTING FULL AUTOMATION PROCESS")
        logger.info("=" * 60)
        
        try:
            # Pre-flight checks
            if not self._perform_preflight_checks():
                logger.critical("Pre-flight checks failed. Aborting execution.")
                return
            
            # Initialize components
            self._initialize_components()
            
            # Process emails
            self._read_and_process_emails()
            
        except Exception as e:
            logger.critical("General error in process", exception=e)
            self._register_general_error(str(e))
        finally:
            # Cleanup
            self._cleanup_resources()
            self._show_summary()
    
    def _perform_preflight_checks(self) -> bool:
        """Perform pre-flight checks before starting automation."""
        logger.info("Performing pre-flight checks...")
        
        # Check system resources
        if not ErrorRecovery.check_system_resources():
            logger.error("System resource check failed")
            return False
        
        # Validate credentials
        if not ErrorRecovery.validate_email_credentials(EMAIL_USER, EMAIL_PASSWORD, IMAP_SERVER):
            logger.error("Email credentials validation failed")
            return False
        
        logger.info("Pre-flight checks passed")
        return True
    
    def _initialize_components(self):
        """Initialize RPA components."""
        try:
            validate_credentials()
            logger.info("Credentials validated")
            
            self.automator = WebAutomator(headless=self.headless)
            logger.info(f"Web automator initialized (headless={self.headless})")
            
        except Exception as e:
            logger.error("Failed to initialize components", exception=e)
            raise
    
    @handle_errors(max_retries=2, delay=1.0)
    def _read_and_process_emails(self):
        """Read emails and process each one with Selenium."""
        logger.info("READING EMAILS...")
        
        user = str(EMAIL_USER)
        password = str(EMAIL_PASSWORD)
        server = str(IMAP_SERVER)
        
        try:
            with MailBox(server).login(user, password, initial_folder="INBOX") as mailbox:
                messages = mailbox.fetch(criteria=AND(seen=False), limit=10, reverse=True)
                
                for i, message in enumerate(messages, start=1):
                    if SENDER_FILTER and SENDER_FILTER.lower() in message.from_.lower():
                        logger.info(f"PROCESSING EMAIL #{i}")
                        logger.info(f"   From: {message.from_}")
                        logger.info(f"   Subject: {message.subject}")
                        self._process_single_email(message, i)
                        
        except Exception as e:
            logger.error("Error reading emails", exception=e)
            raise EmailConnectionError(f"Failed to read emails: {str(e)}")
    
    def _process_single_email(self, message, number):
        """Process a single email with web automation."""
        process_id = get_next_process_id()
        extracted_content = message.text[:5000] + "..." if len(message.text) > 5000 else message.text
        
        try:
            logger.info(f"   Process ID: {process_id}")
            logger.info(f"   Extracted content: {len(extracted_content)} characters")
            
            # Extract links
            links = extract_links(message.text)
            logger.info(f"   Links found: {len(links)}")
            
            if not links:
                logger.warning("No links found in email")
                self._register_email_result(message, extracted_content, "", "No links found", "", "No links", process_id)
                return
            
            # Process each link
            for link in links:
                logger.info(f"   Processing URL: {link}")
                self._process_url(link, message, extracted_content, process_id)
                
        except Exception as e:
            logger.error(f"Error processing email #{number}", exception=e)
            self._register_email_result(message, extracted_content, "", "Error", str(e), "Processing failed", process_id)
            self.total_errors += 1
            self.error_details.append({
                'type': 'Email Processing Error',
                'message': str(e),
                'context': f'Email #{number}',
                'timestamp': datetime.now().isoformat()
            })
    
    @handle_errors(max_retries=2, delay=1.0)
    def _process_url(self, url, message, extracted_content, process_id):
        """Process a single URL with web automation."""
        try:
            # Validate URL
            logger.info(f"Validating URL: {url}")
            response = requests.head(url, timeout=10)
            if response.status_code >= 400:
                raise WebAutomationError(f"URL returned status code {response.status_code}")
            
            # Open URL and perform automation
            if self.automator:
                success = self.automator.open_link(url)
                if not success:
                    raise WebAutomationError("Failed to open URL")
                
                # Get page title
                title = self.automator.get_page_title()
                logger.info(f"Page title: {title}")
                
                # Try to click buttons
                click_success = self._attempt_button_clicks()
                
                # Get final result
                final_result = "Success" if click_success else "Partial success"
                self._register_email_result(message, extracted_content, url, "Success", "", final_result, process_id)
                self.total_success += 1
                
            else:
                raise WebAutomationError("Web automator not initialized")
                
        except Exception as e:
            logger.error(f"Error processing URL: {url}", exception=e)
            self._register_email_result(message, extracted_content, url, "Error", str(e), "URL processing failed", process_id)
            self.total_errors += 1
    
    def _attempt_button_clicks(self) -> bool:
        """Attempt to click buttons on the page."""
        try:
            selectors_to_test = [
                "//button[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]",
                "//a[contains(text(), 'Click') or contains(text(), 'Submit') or contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Continue') or contains(text(), 'Next') or contains(text(), 'Accept') or contains(text(), 'OK')]",
                "//button",
                "//a[contains(@href, '#') or contains(@href, 'javascript')]",
                BUTTON_SELECTOR
            ]
            
            for selector in selectors_to_test:
                if self.automator.click_button(selector, SELECTOR_TYPE, f"button with selector: {selector}"):
                    result = self.automator.get_last_click_result()
                    logger.info(f"Button click successful: {result}")
                    return True
            
            logger.warning("No clickable buttons found")
            return False
            
        except Exception as e:
            logger.error("Error during button clicking", exception=e)
            return False
    
    def _register_email_result(self, message, content, url, status, error_detail, final_result, process_id):
        """Register email processing result in database."""
        try:
            save_record(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                message.from_,
                message.subject,
                content,
                url,
                status,
                error_detail,
                final_result,
                process_id
            )
            logger.info(f"Record saved: {status} - ID: {process_id}")
            
        except Exception as e:
            logger.error("Error saving to database", exception=e)
    
    def _register_general_error(self, error_msg):
        """Register general system errors in database."""
        try:
            process_id = get_next_process_id()
            save_record(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "SYSTEM",
                "ERROR_GENERAL",
                "System error",
                "",
                "Error",
                f"System error: {error_msg}",
                "General failure",
                process_id
            )
        except Exception as e:
            logger.error("Error registering general error", exception=e)
    
    def _cleanup_resources(self):
        """Clean up resources."""
        try:
            if self.automator:
                self.automator.close_browser()
                logger.info("Web automator browser closed")
        except Exception as e:
            logger.error("Error during cleanup", exception=e)
    
    def _show_summary(self):
        """Show RPA process summary."""
        execution_time = time.time() - self.start_time
        
        logger.info("FULL AUTOMATION PROCESS SUMMARY")
        logger.info("=" * 40)
        logger.info(f"Emails processed: {self.total_processed}")
        logger.info(f"Successes: {self.total_success}")
        logger.info(f"Errors: {self.total_errors}")
        
        if self.total_processed > 0:
            success_rate = (self.total_success / self.total_processed) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        logger.info(f"Execution time: {execution_time:.2f} seconds")
        
        # Log system status
        logger.log_system_status(self.total_processed, self.total_success, self.total_errors, execution_time)
        
        # Create error report if there were errors
        if self.error_details:
            error_report = create_error_report(self.total_errors, self.error_details)
            logger.info("Error report generated")
            logger.debug(error_report)
        
        logger.info("FULL AUTOMATION PROCESS COMPLETED")

def run_full_rpa(headless=True, debug=True):
    """
    Run the complete RPA process.
    Args:
        headless (bool): Run in headless mode
        debug (bool): Show detailed information
    """
    rpa = FullRPA(headless=headless, debug=debug)
    rpa.process_emails_automatically()

if __name__ == "__main__":
    logger.info("FULL RPA SYSTEM")
    logger.info("=" * 30)
    logger.info("This system will automatically process emails")
    logger.info("and execute web actions with Selenium.")
    logger.info("")
    
    if HEADLESS_MODE:
        logger.info("Executing in headless mode...")
    else:
        logger.info("Executing with browser window...")
    
    logger.info("Press Ctrl+C to cancel if necessary.")
    logger.info("")
    
    try:
        run_full_rpa(headless=HEADLESS_MODE, debug=DEBUG_MODE)
        logger.info("Waiting 10 minutes for the next execution...")
        time.sleep(600)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.critical("Unexpected error in main execution", exception=e) 