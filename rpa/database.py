#!/usr/bin/env python3
"""
Módulo para manejo de base de datos SQLite
Contiene funciones para crear tablas e insertar registros del proceso RPA.
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import pandas as pd

logger = logging.getLogger(__name__)

class Database:
    """
    Clase para manejar la base de datos SQLite del sistema RPA.
    """
    
    def __init__(self, db_path: str = "rpa_database.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.connection = None
        self._create_table()
    
    def _create_table(self):
        """
        Crea las tablas principales si no existen.
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()

            # Crear tabla para procesos exitosos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rpa_success (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT NOT NULL,
                    subject TEXT,
                    link TEXT,
                    status TEXT NOT NULL,
                    observations TEXT,
                    processing_time REAL
                )
            ''')

            # Crear tabla para procesos fallidos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rpa_failed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sender TEXT NOT NULL,
                    subject TEXT,
                    link TEXT,
                    status TEXT NOT NULL,
                    observations TEXT,
                    error_details TEXT,
                    processing_time REAL
                )
            ''')

            # Crear tabla de configuración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')



            self.connection.commit()
            logger.info("Tablas de base de datos creadas/verificadas exitosamente")

        except Exception as e:
            logger.error(f"Error creando tablas: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()

    def insert_success_record(self, sender: str, subject: str, link: str, 
                             status: str, observations: str = "", processing_time: float = 0.0) -> bool:
        """
        Inserta un nuevo registro exitoso en la base de datos.
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO rpa_success 
                (sender, subject, link, status, observations, processing_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sender, subject, link, status, observations, processing_time))
            self.connection.commit()
            logger.info(f"Registro exitoso insertado: {sender} - {status}")
            return True
        except Exception as e:
            logger.error(f"Error insertando registro exitoso: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()

    def insert_failed_record(self, sender: str, subject: str, link: str, 
                            status: str, observations: str = "", error_details: str = "", processing_time: float = 0.0) -> bool:
        """
        Inserta un nuevo registro fallido en la base de datos.
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO rpa_failed 
                (sender, subject, link, status, observations, error_details, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sender, subject, link, status, observations, error_details, processing_time))
            self.connection.commit()
            logger.info(f"Registro fallido insertado: {sender} - {status}")
            return True
        except Exception as e:
            logger.error(f"Error insertando registro fallido: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()
    
    def get_recent_records(self, limit: int = 10) -> list:
        """
        Obtiene los registros más recientes de la base de datos.
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            list: Lista de registros recientes
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM rpa_records 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            records = cursor.fetchall()
            return records
            
        except Exception as e:
            logger.error(f"Error obteniendo registros: {str(e)}")
            return []
        finally:
            if self.connection:
                self.connection.close()
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas del sistema RPA.
        
        Returns:
            dict: Diccionario con estadísticas
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # Total de registros
            cursor.execute('SELECT COUNT(*) FROM rpa_records')
            total_records = cursor.fetchone()[0]
            
            # Registros por estado
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM rpa_records 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Registros de hoy
            cursor.execute('''
                SELECT COUNT(*) 
                FROM rpa_records 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            today_records = cursor.fetchone()[0]
            
            return {
                'total_records': total_records,
                'status_counts': status_counts,
                'today_records': today_records
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}
        finally:
            if self.connection:
                self.connection.close()
    
    def update_config(self, key: str, value: str) -> bool:
        """
        Actualiza o inserta una configuración en la base de datos.
        
        Args:
            key: Clave de configuración
            value: Valor de configuración
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            
            self.connection.commit()
            logger.info(f"Configuración actualizada: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()
    
    def get_config(self, key: str) -> Optional[str]:
        """
        Obtiene una configuración de la base de datos.
        
        Args:
            key: Clave de configuración
            
        Returns:
            Optional[str]: Valor de configuración o None si no existe
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {str(e)}")
            return None
        finally:
            if self.connection:
                self.connection.close() 

    def delete_old_records(self, days: int = 30) -> int:
        """
        Elimina los registros de rpa_records con más de 'days' días de antigüedad.
        
        Args:
            days: Número de días de antigüedad para conservar los registros
        Returns:
            int: Número de registros eliminados
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM rpa_records
                WHERE timestamp < datetime('now', ?)
            ''', (f'-{days} days',))
            deleted = cursor.rowcount
            self.connection.commit()
            logger.info(f"Registros eliminados por antigüedad (> {days} días): {deleted}")
            return deleted
        except Exception as e:
            logger.error(f"Error eliminando registros antiguos: {str(e)}")
            return 0
        finally:
            if self.connection:
                self.connection.close() 

    def export_to_excel(self, excel_path: str = "reporte_rpa.xlsx") -> str:
        """
        Exporta las tablas rpa_success y rpa_failed a un archivo Excel con dos hojas.
        Args:
            excel_path: Ruta del archivo Excel a crear
        Returns:
            str: Ruta del archivo generado
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            # Leer ambas tablas a DataFrames
            df_success = pd.read_sql_query("SELECT * FROM rpa_success", self.connection)
            df_failed = pd.read_sql_query("SELECT * FROM rpa_failed", self.connection)
            # Escribir a Excel con dos hojas
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df_success.to_excel(writer, sheet_name="Exitosos", index=False)
                df_failed.to_excel(writer, sheet_name="Fallidos", index=False)
            return excel_path
        except Exception as e:
            logger.error(f"Error exportando a Excel: {str(e)}")
            return ""
        finally:
            if self.connection:
                self.connection.close()




 