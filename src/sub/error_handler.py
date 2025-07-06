"""
Error handling and recovery system for RPA automation.
"""
from typing import Optional, Callable, Any
from functools import wraps
import time
from .logger import get_logger

logger = get_logger()

class RPAError(Exception):
    """Base exception class for RPA errors."""
    pass

class EmailConnectionError(RPAError):
    """Raised when there's an error connecting to email server."""
    pass

class WebAutomationError(RPAError):
    """Raised when there's an error in web automation."""
    pass

class DatabaseError(RPAError):
    """Raised when there's an error in database operations."""
    pass

class ConfigurationError(RPAError):
    """Raised when there's an error in configuration."""
    pass

class RetryableError(RPAError):
    """Raised when an operation can be retried."""
    pass

def handle_errors(max_retries: int = 3, delay: float = 1.0, 
                 retry_exceptions: tuple = (RetryableError, ConnectionError, TimeoutError)):
    """
    Decorator to handle errors with automatic retry logic.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        delay (float): Delay between retries in seconds
        retry_exceptions (tuple): Exceptions that should trigger a retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                     f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}")
                        raise
                except Exception as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}", exception=e)
                    raise
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_return: Any = None, 
                error_message: str = "Function execution failed", **kwargs) -> Any:
    """
    Safely execute a function and return a default value if it fails.
    
    Args:
        func (Callable): Function to execute
        *args: Arguments for the function
        default_return (Any): Default value to return if function fails
        error_message (str): Error message to log
        **kwargs: Keyword arguments for the function
    
    Returns:
        Any: Function result or default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exception=e)
        return default_return

class ErrorRecovery:
    """Class to handle error recovery strategies."""
    
    @staticmethod
    def validate_email_credentials(email_user: str, email_password: str, imap_server: str) -> bool:
        """
        Validate email credentials before processing.
        
        Args:
            email_user (str): Email username
            email_password (str): Email password
            imap_server (str): IMAP server address
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            if not all([email_user, email_password, imap_server]):
                raise ConfigurationError("Missing email credentials")
            
            # Basic validation
            if '@' not in email_user:
                raise ConfigurationError("Invalid email format")
            
            if len(email_password) < 8:
                raise ConfigurationError("Password too short")
            
            logger.info("Email credentials validation passed")
            return True
            
        except Exception as e:
            logger.error("Email credentials validation failed", exception=e)
            return False
    
    @staticmethod
    def check_system_resources() -> bool:
        """
        Check if system has enough resources to run RPA.
        
        Returns:
            bool: True if system is ready, False otherwise
        """
        try:
            import psutil
            
            # Check available memory (at least 500MB)
            memory = psutil.virtual_memory()
            if memory.available < 500 * 1024 * 1024:  # 500MB
                logger.warning(f"Low memory available: {memory.available / 1024 / 1024:.1f}MB")
                return False
            
            # Check disk space (at least 100MB)
            disk = psutil.disk_usage('/')
            if disk.free < 100 * 1024 * 1024:  # 100MB
                logger.warning(f"Low disk space: {disk.free / 1024 / 1024:.1f}MB")
                return False
            
            logger.info("System resources check passed")
            return True
            
        except ImportError:
            logger.warning("psutil not available, skipping system resource check")
            return True
        except Exception as e:
            logger.error("System resource check failed", exception=e)
            return False
    
    @staticmethod
    def cleanup_resources(automator=None, database_connection=None):
        """
        Clean up resources in case of errors.
        
        Args:
            automator: Web automator instance to close
            database_connection: Database connection to close
        """
        try:
            if automator and hasattr(automator, 'close_browser'):
                automator.close_browser()
                logger.info("Web automator browser closed")
            
            if database_connection and hasattr(database_connection, 'close'):
                database_connection.close()
                logger.info("Database connection closed")
                
        except Exception as e:
            logger.error("Error during resource cleanup", exception=e)

def log_error_context(context: str, error: Exception, additional_info: dict = None):
    """
    Log error with context information.
    
    Args:
        context (str): Context where the error occurred
        error (Exception): The error that occurred
        additional_info (dict): Additional information to log
    """
    error_info = {
        'context': context,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': time.time()
    }
    
    if additional_info:
        error_info.update(additional_info)
    
    logger.error(f"Error in {context}: {str(error)}", exception=error)
    logger.debug(f"Error context: {error_info}")

def create_error_report(total_errors: int, error_details: list) -> str:
    """
    Create a formatted error report.
    
    Args:
        total_errors (int): Total number of errors
        error_details (list): List of error details
    
    Returns:
        str: Formatted error report
    """
    report = f"ERROR REPORT - Total Errors: {total_errors}\n"
    report += "=" * 50 + "\n"
    
    for i, error in enumerate(error_details, 1):
        report += f"Error #{i}:\n"
        report += f"  Type: {error.get('type', 'Unknown')}\n"
        report += f"  Message: {error.get('message', 'No message')}\n"
        report += f"  Context: {error.get('context', 'Unknown')}\n"
        report += f"  Timestamp: {error.get('timestamp', 'Unknown')}\n"
        report += "-" * 30 + "\n"
    
    return report 