"""
Utilidades de base de datos para el RPA: creación de tablas, inserción de registros y generación de IDs de proceso.
"""
import sqlite3
from datetime import datetime

def create_table():
    """Crea la tabla 'records' si no existe."""
    conexion = sqlite3.connect('rpa.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            sender TEXT,
            subject TEXT,
            message_content TEXT,
            extracted_url TEXT,
            status TEXT,
            detailed_error TEXT,
            final_result TEXT,
            process_id TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

def save_record(datetime, sender, subject, message_content, extracted_url, status, detailed_error, final_result, process_id):
    """Inserta un nuevo registro en la tabla 'records'."""
    conexion = sqlite3.connect('rpa.db')
    cursor = conexion.cursor()
    
    # Crear tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            sender TEXT,
            subject TEXT,
            message_content TEXT,
            extracted_url TEXT,
            status TEXT,
            detailed_error TEXT,
            final_result TEXT,
            process_id TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO records (
            datetime, sender, subject, message_content, extracted_url, status, detailed_error, final_result, process_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime, sender, subject, message_content, extracted_url, status, detailed_error, final_result, process_id))
    conexion.commit()
    conexion.close()

def get_next_process_id():
    """Genera un ID de proceso único para cada ejecución del RPA."""
    import uuid
    return f"RPA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

if __name__ == "__main__":
    create_table()
