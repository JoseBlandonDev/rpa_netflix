"""
Read emails from IMAP server, extract links and record results in database.
"""
from sub.database import save_record
from sub.logger import get_logger
from sub.error_handler import handle_errors, safe_execute, EmailConnectionError, ConfigurationError
from datetime import datetime
from imap_tools.mailbox import MailBox
from imap_tools.query import AND
from dotenv import load_dotenv
import os
import re
from bs4 import BeautifulSoup, Tag

load_dotenv()

# Get logger instance
logger = get_logger()

# Environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
SENDER_FILTER = os.getenv("SENDER_FILTER")
BUTTON_TEXT = os.getenv("BUTTON_TEXT")
URL_PATTERN = os.getenv("URL_PATTERN")

@handle_errors(max_retries=2, delay=1.0)
def validate_credentials():
    """Validate that all required credentials are configured."""
    if not EMAIL_USER or not EMAIL_PASSWORD or not IMAP_SERVER:
        raise ConfigurationError("Missing credentials in .env file. Check EMAIL_USER, EMAIL_PASSWORD, and IMAP_SERVER")
    
    logger.info("Email credentials validation passed")
    return True

def extract_links(text):
    """Extract all URLs that match the specified pattern, or all URLs if no pattern is set."""
    if URL_PATTERN:
        pattern = re.escape(URL_PATTERN) + r"[\w\-\?&=/%#\.]+"
        links = re.findall(pattern, text)
        logger.debug(f"Extracted {len(links)} links matching pattern: {URL_PATTERN}")
        return links
    
    # Default pattern for all URLs
    pattern = r'https?://[^\s]+'
    links = re.findall(pattern, text)
    logger.debug(f"Extracted {len(links)} links using default pattern")
    return links

@handle_errors(max_retries=3, delay=2.0)
def read_unread_filtered_emails():
    """Read unread emails, filter by sender, extract links and record results."""
    try:
        validate_credentials()
        
        user = str(EMAIL_USER)
        password = str(EMAIL_PASSWORD)
        server = str(IMAP_SERVER)
        
        logger.info(f"Connecting to email server: {server}")
        
        with MailBox(server).login(user, password, initial_folder="INBOX") as mailbox:
            messages = mailbox.fetch(criteria=AND(seen=False), limit=10, reverse=True)
            
            for i, message in enumerate(messages, start=1):
                if SENDER_FILTER and SENDER_FILTER.lower() in message.from_.lower():
                    logger.info(f"Processing email #{i}")
                    logger.info(f"From: {message.from_}")
                    logger.info(f"Subject: {message.subject}")
                    logger.info(f"Date: {message.date}")
                    
                    # Extract content
                    content = message.text[:300] if message.text else "No text content"
                    logger.debug(f"Content preview: {content}")
                    
                    # Extract links
                    links = extract_links(message.text or "")
                    
                    if links:
                        logger.info(f"Found {len(links)} links:")
                        for link in links:
                            logger.info(f"  ➡️ {link}")
                    else:
                        logger.warning("No links found in this email")
                    
                    # Save to database
                    try:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        sender = message.from_
                        subject = message.subject
                        all_links = ", ".join(links)
                        extracted_link = links[0] if links else ""
                        status = "Success"
                        observations = "Processed successfully"
                        
                        save_record(
                            timestamp, sender, subject, extracted_link, 
                            all_links, status, observations
                        )
                        
                        logger.info(f"Email #{i} processed and saved to database")
                        
                    except Exception as e:
                        logger.error(f"Error saving email #{i} to database", exception=e)
                        
    except Exception as e:
        logger.error("Error reading emails", exception=e)
        raise EmailConnectionError(f"Failed to read emails: {str(e)}")

def test_email_connection():
    """Test email connection and credentials."""
    try:
        validate_credentials()
        
        user = str(EMAIL_USER)
        password = str(EMAIL_PASSWORD)
        server = str(IMAP_SERVER)
        
        logger.info("Testing email connection...")
        
        with MailBox(server).login(user, password, initial_folder="INBOX") as mailbox:
            # Try to get folder info
            folder_info = mailbox.folder()
            logger.info(f"Successfully connected to: {folder_info.name}")
            
            # Count unread messages
            unread_count = len(list(mailbox.fetch(criteria=AND(seen=False))))
            logger.info(f"Unread messages: {unread_count}")
            
            return True
            
    except Exception as e:
        logger.error("Email connection test failed", exception=e)
        return False

if __name__ == "__main__":
    logger.info("Testing email reader module...")
    
    if test_email_connection():
        logger.info("Email connection test passed")
        read_unread_filtered_emails()
    else:
        logger.error("Email connection test failed")
