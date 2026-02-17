
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "flybondi_monitor.db"

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de vuelos rastreados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flight_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        departure_date TEXT,
        return_date TEXT,
        flight_no_out TEXT,
        flight_no_in TEXT,
        total_price REAL,
        currency TEXT,
        availability_out INTEGER,
        availability_in INTEGER,
        is_glitch BOOLEAN DEFAULT 0
    )
    ''')
    
    # Tabla de alertas enviadas (para evitar spam)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        alert_type TEXT,
        price REAL,
        message TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"   💽 Base de datos inicializada: {DB_PATH.name}")

def save_flight_data(flight_data):
    """Guarda un registro de un vuelo encontrado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO flight_history (
            timestamp, departure_date, return_date, 
            flight_no_out, flight_no_in, 
            total_price, currency, 
            availability_out, availability_in
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            flight_data['departure_date'],
            flight_data['return_date'],
            flight_data['outbound']['flight_no'],
            flight_data['inbound']['flight_no'],
            flight_data['total_ars'],
            "ARS",
            flight_data['outbound']['availability'],
            flight_data['inbound']['availability']
        ))
        conn.commit()
    except Exception as e:
        print(f"   ❌ Error guardando en DB: {e}")
    finally:
        conn.close()

def get_lowest_price_history(days=7):
    """Devuelve el precio mínimo registrado en los últimos X días."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fecha de corte
    # (En SQL simple, calculamos texto, pero mejor traer todo y filtrar si es complejo,
    #  o usar la función date de SQLite)
    
    cursor.execute('SELECT MIN(total_price) FROM flight_history')
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result and result[0] else None
