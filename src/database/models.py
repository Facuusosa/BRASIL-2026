"""
models.py - Modelos de datos SQLAlchemy para el Flight Monitor Bot

Define las tablas de la base de datos SQLite:
- flights: Vuelos encontrados por los scrapers
- price_history: Histórico de precios para análisis de tendencias
- alerts_sent: Registro de alertas enviadas por Telegram

RESTRICCIÓN: Solo se almacenan precios y datos públicos.
NUNCA se guardan datos de tarjetas, cuentas o información de pago.
"""

import json
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

from src.config import DATABASE_PATH

# Base declarativa de SQLAlchemy
Base = declarative_base()


class Flight(Base):
    """
    Modelo para vuelos encontrados por los scrapers.
    
    Cada registro representa una opción de vuelo encontrada en una búsqueda,
    con toda la información relevante: aerolínea, precio, horarios, etc.
    """
    
    __tablename__ = "flights"
    
    # --- Identificadores ---
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # --- Plataforma de origen ---
    platform = Column(String(50), nullable=False, index=True)
    # Ej: "Turismo City", "Despegar"
    
    # --- Aerolíneas ---
    # Se guarda como JSON string: '["Flybondi", "JetSmart"]'
    airlines_json = Column(Text, nullable=False)
    
    # --- Precios ---
    price_usd = Column(Float, nullable=True, index=True)
    price_ars = Column(Float, nullable=True)
    
    # --- Horarios IDA ---
    outbound_departure = Column(String(20), nullable=True)
    # Formato: "HH:MM" o "YYYY-MM-DD HH:MM"
    outbound_arrival = Column(String(20), nullable=True)
    
    # --- Horarios VUELTA ---
    return_departure = Column(String(20), nullable=True)
    return_arrival = Column(String(20), nullable=True)
    
    # --- Detalles del vuelo ---
    flight_type = Column(String(20), default="direct")
    # Valores: "direct", "1_stop", "2+_stops"
    
    origin_airport = Column(String(5), nullable=True)
    # Ej: "AEP", "EZE"
    
    destination_airport = Column(String(5), default="FLN")
    
    return_airport = Column(String(5), nullable=True)
    # Ej: "AEP", "EZE" (aeropuerto de llegada en la vuelta)
    
    duration_minutes = Column(Integer, nullable=True)
    
    # --- Disponibilidad ---
    availability = Column(String(50), nullable=True)
    # Ej: "Últimos 3 asientos", None si no lo muestra
    
    # --- Equipaje ---
    luggage_included = Column(Boolean, default=False)
    
    # --- Score calculado ---
    score = Column(Float, nullable=True)
    # Score de 0-100 calculado por el FlightScorer
    
    # --- URL de referencia ---
    url = Column(Text, nullable=True)
    
    # --- Fechas de búsqueda ---
    departure_date = Column(String(10), nullable=True)
    # La fecha del vuelo de ida: "2026-03-09"
    
    return_date = Column(String(10), nullable=True)
    # La fecha del vuelo de vuelta: "2026-03-16"
    
    # --- Metadatos ---
    search_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # --- Relaciones ---
    price_history = relationship("PriceHistory", back_populates="flight", cascade="all, delete-orphan")
    alerts = relationship("AlertSent", back_populates="flight", cascade="all, delete-orphan")
    
    # --- Índices compuestos para queries frecuentes ---
    __table_args__ = (
        Index("idx_platform_date", "platform", "departure_date"),
        Index("idx_price_search", "price_usd", "search_timestamp"),
    )
    
    @property
    def airlines(self) -> list[str]:
        """Devuelve la lista de aerolíneas (deserializa JSON)."""
        try:
            return json.loads(self.airlines_json) if self.airlines_json else []
        except json.JSONDecodeError:
            return [self.airlines_json] if self.airlines_json else []
    
    @airlines.setter
    def airlines(self, value: list[str]):
        """Guarda la lista de aerolíneas como JSON."""
        if isinstance(value, list):
            self.airlines_json = json.dumps(value)
        else:
            self.airlines_json = json.dumps([str(value)])
    
    def __repr__(self):
        return (
            f"<Flight id={self.id} airlines={self.airlines} "
            f"price_usd={self.price_usd} platform='{self.platform}'>"
        )


class PriceHistory(Base):
    """
    Histórico de precios para análisis de tendencias.
    
    Cada vez que se encuentra el mismo vuelo en una búsqueda posterior,
    se registra el nuevo precio aquí para detectar subidas/bajadas.
    """
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia al vuelo
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)
    
    # Precio registrado en este momento
    price_usd = Column(Float, nullable=True)
    price_ars = Column(Float, nullable=True)
    
    # Timestamp del registro
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relación
    flight = relationship("Flight", back_populates="price_history")
    
    def __repr__(self):
        return (
            f"<PriceHistory flight_id={self.flight_id} "
            f"price_usd={self.price_usd} at={self.timestamp}>"
        )


class AlertSent(Base):
    """
    Registro de alertas enviadas por Telegram.
    
    Permite evitar enviar alertas duplicadas y llevar un historial
    de todas las notificaciones enviadas al usuario.
    """
    
    __tablename__ = "alerts_sent"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia al vuelo que disparó la alerta
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)
    
    # Tipo de alerta
    alert_type = Column(String(20), nullable=False)
    # Valores: "critical", "important", "info", "daily_report", "error"
    
    # Timestamp de envío
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # ID del mensaje en Telegram (para referencia)
    telegram_message_id = Column(Integer, nullable=True)
    
    # Contenido del mensaje (por si hay que debuggear)
    message_preview = Column(Text, nullable=True)
    
    # Relación
    flight = relationship("Flight", back_populates="alerts")
    
    def __repr__(self):
        return (
            f"<AlertSent type='{self.alert_type}' "
            f"flight_id={self.flight_id} at={self.sent_at}>"
        )


def create_database():
    """
    Crea todas las tablas en la base de datos SQLite.
    Se puede ejecutar directamente: python src/database/models.py
    """
    engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
    Base.metadata.create_all(engine)
    print(f"✅ Base de datos creada en: {DATABASE_PATH}")
    print(f"   Tablas: flights, price_history, alerts_sent")
    return engine


if __name__ == "__main__":
    create_database()
