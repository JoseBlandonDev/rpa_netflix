"""
Advanced logging system for RPA automation with error handling and file rotation.
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
import traceback
import sys

class RPALogger:
    """
    Advanced logger for RPA automation with file rotation and error handling.
    """
    
    def __init__(self, name: str = "RPA_Automation", log_level: str = "INFO", 
                 log_dir: str = "logs", max_bytes: int = 10*1024*1024, backup_count: int = 5):
        """
        Initialize the RPA logger.
        
        Args:
            name (str): Logger name
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir (str): Directory to store log files
            max_bytes (int): Maximum size of log file before rotation
            backup_count (int): Number of backup files to keep
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup and configure the logger with file rotation and console output."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler (simple format)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        log_filename = os.path.join(self.log_dir, f"rpa_automation_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error file handler (only errors and critical)
        error_filename = os.path.join(self.log_dir, f"rpa_errors_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_filename,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        return logger
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log error message with optional exception details."""
        if exception:
            error_details = f"{message} - Exception: {str(exception)} - Traceback: {traceback.format_exc()}"
            self.logger.error(error_details)
        else:
            self.logger.error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log critical error message with optional exception details."""
        if exception:
            error_details = f"CRITICAL: {message} - Exception: {str(exception)} - Traceback: {traceback.format_exc()}"
            self.logger.critical(error_details)
        else:
            self.logger.critical(f"CRITICAL: {message}")
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def log_email_processing(self, email_number: int, sender: str, subject: str, 
                           links_found: int, status: str) -> None:
        """Log email processing details."""
        self.info(f"Email #{email_number} processed - From: {sender} - Subject: {subject} - "
                 f"Links: {links_found} - Status: {status}")
    
    def log_web_automation(self, url: str, action: str, success: bool, 
                          details: str = "") -> None:
        """Log web automation actions."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Web automation - URL: {url} - Action: {action} - Status: {status} - Details: {details}")
    
    def log_database_operation(self, operation: str, success: bool, 
                              details: str = "") -> None:
        """Log database operations."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Database operation - {operation} - Status: {status} - Details: {details}")
    
    def log_system_status(self, total_processed: int, total_success: int, 
                         total_errors: int, execution_time: float) -> None:
        """Log system execution summary."""
        success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
        self.info(f"System execution completed - Processed: {total_processed}, "
                 f"Success: {total_success}, Errors: {total_errors}, "
                 f"Success Rate: {success_rate:.1f}%, Execution Time: {execution_time:.2f}s")

# Global logger instance
rpa_logger = RPALogger()

def get_logger() -> RPALogger:
    """Get the global RPA logger instance."""
    return rpa_logger 