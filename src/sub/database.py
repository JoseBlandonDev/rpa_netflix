"""
Database operations for RPA automation: save records and manage process IDs.
"""
import sqlite3
import os
from datetime import datetime
from sub.logger import get_logger
from sub.error_handler import handle_errors, safe_execute, DatabaseError

# Get logger instance
logger = get_logger()

DATABASE_FILE = "rpa.db"

def create_database():
    """Create the database and tables if they don't exist."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Create main table for RPA records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rpa_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                sender TEXT NOT NULL,
                subject TEXT,
                message_content TEXT,
                extracted_url TEXT,
                status TEXT NOT NULL,
                detailed_error TEXT,
                final_result TEXT,
                process_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_process_id ON rpa_records(process_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_datetime ON rpa_records(datetime)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Error creating database", exception=e)
        raise DatabaseError(f"Failed to create database: {str(e)}")

@handle_errors(max_retries=3, delay=1.0)
def save_record(datetime_str, sender, subject, message_content, extracted_url, 
                status, detailed_error, final_result, process_id):
    """
    Save a record to the database.
    
    Args:
        datetime_str (str): Date and time string
        sender (str): Email sender
        subject (str): Email subject
        message_content (str): Email content
        extracted_url (str): Extracted URL
        status (str): Processing status
        detailed_error (str): Detailed error information
        final_result (str): Final result
        process_id (str): Process ID
    """
    try:
        # Ensure database exists
        if not os.path.exists(DATABASE_FILE):
            create_database()
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rpa_records 
            (datetime, sender, subject, message_content, extracted_url, status, detailed_error, final_result, process_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime_str, sender, subject, message_content, extracted_url, status, detailed_error, final_result, process_id))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Record saved successfully - Process ID: {process_id}")
        
    except Exception as e:
        logger.error("Error saving record to database", exception=e)
        raise DatabaseError(f"Failed to save record: {str(e)}")

def get_next_process_id():
    """
    Generate a unique process ID.
    
    Returns:
        str: Unique process ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    process_id = f"RPA_{timestamp}_{unique_id}"
    
    logger.debug(f"Generated process ID: {process_id}")
    return process_id

def get_recent_records(limit=10):
    """
    Get recent records from the database.
    
    Args:
        limit (int): Number of records to retrieve
    
    Returns:
        list: List of recent records
    """
    try:
        if not os.path.exists(DATABASE_FILE):
            logger.warning("Database file does not exist")
            return []
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT datetime, sender, subject, status, final_result, process_id
            FROM rpa_records
            ORDER BY datetime DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        logger.debug(f"Retrieved {len(records)} recent records")
        return records
        
    except Exception as e:
        logger.error("Error retrieving recent records", exception=e)
        return []

def get_total_records():
    """
    Get total number of records in the database.
    
    Returns:
        int: Total number of records
    """
    try:
        if not os.path.exists(DATABASE_FILE):
            return 0
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM rpa_records')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.debug(f"Total records in database: {count}")
        return count
        
    except Exception as e:
        logger.error("Error counting total records", exception=e)
        return 0

def get_error_records(limit=10):
    """
    Get records with errors from the database.
    
    Args:
        limit (int): Number of error records to retrieve
    
    Returns:
        list: List of error records
    """
    try:
        if not os.path.exists(DATABASE_FILE):
            return []
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT datetime, sender, subject, detailed_error, process_id
            FROM rpa_records
            WHERE status = 'Error'
            ORDER BY datetime DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        logger.debug(f"Retrieved {len(records)} error records")
        return records
        
    except Exception as e:
        logger.error("Error retrieving error records", exception=e)
        return []

def cleanup_old_records(days_to_keep=30):
    """
    Clean up old records from the database.
    
    Args:
        days_to_keep (int): Number of days to keep records
    """
    try:
        if not os.path.exists(DATABASE_FILE):
            logger.warning("Database file does not exist")
            return
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Delete records older than specified days
        cursor.execute('''
            DELETE FROM rpa_records
            WHERE datetime < date('now', '-{} days')
        '''.format(days_to_keep))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old records (older than {days_to_keep} days)")
        else:
            logger.debug("No old records to clean up")
            
    except Exception as e:
        logger.error("Error cleaning up old records", exception=e)

if __name__ == "__main__":
    logger.info("Testing database module...")
    
    try:
        # Create database
        create_database()
        
        # Test save record
        test_process_id = get_next_process_id()
        save_record(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test@example.com",
            "Test Subject",
            "Test content",
            "https://example.com",
            "Test",
            "",
            "Test result",
            test_process_id
        )
        
        # Test get records
        total = get_total_records()
        recent = get_recent_records(5)
        
        logger.info(f"Database test completed - Total records: {total}, Recent records: {len(recent)}")
        
    except Exception as e:
        logger.error("Database test failed", exception=e)
