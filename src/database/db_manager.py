"""
db_manager.py - Gestor de base de datos del Flight Monitor Bot

Encapsula todas las operaciones CRUD sobre la base de datos SQLite:
- Guardar vuelos encontrados
- Consultar histórico de precios
- Registrar alertas enviadas
- Limpiar registros viejos (>30 días)
- Obtener estadísticas y tendencias

Uso:
    from src.database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.save_flight(flight_dict)
    recent = db.get_recent_flights(hours=24)
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session

from src.config import DATABASE_PATH, DB_CLEANUP_DAYS
from src.database.models import Base, Flight, PriceHistory, AlertSent
from src.utils.logger import get_database_logger

logger = get_database_logger()


class DatabaseManager:
    """
    Gestor de la base de datos SQLite del bot.
    
    Maneja el ciclo de vida de las sesiones SQLAlchemy y proporciona
    métodos de alto nivel para todas las operaciones de datos.
    """
    
    def __init__(self, db_path: str = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta a la base de datos SQLite (default: config.DATABASE_PATH)
        """
        self.db_path = db_path or DATABASE_PATH
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            # Optimizaciones para SQLite
            connect_args={"check_same_thread": False},
        )
        
        # Crear tablas si no existen
        Base.metadata.create_all(self.engine)
        
        # Crear factory de sesiones
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"💾 Base de datos inicializada: {self.db_path}")
    
    def _get_session(self) -> Session:
        """Crea una nueva sesión de base de datos."""
        return self.SessionLocal()
    
    # ====================================================================
    # OPERACIONES CON VUELOS
    # ====================================================================
    
    def save_flight(self, flight_data: dict) -> Optional[int]:
        """
        Guarda un vuelo encontrado en la base de datos.
        
        También registra el precio en el histórico (price_history)
        para análisis de tendencias.
        
        Args:
            flight_data: Diccionario con los datos del vuelo
                         (formato del output de los scrapers)
        
        Returns:
            int: ID del vuelo guardado, o None si hubo error
        """
        session = self._get_session()
        
        try:
            # Crear objeto Flight
            flight = Flight(
                platform=flight_data.get("platform", "Desconocida"),
                price_usd=flight_data.get("price_usd"),
                price_ars=flight_data.get("price_ars"),
                outbound_departure=flight_data.get("outbound_departure", ""),
                outbound_arrival=flight_data.get("outbound_arrival", ""),
                return_departure=flight_data.get("return_departure", ""),
                return_arrival=flight_data.get("return_arrival", ""),
                flight_type=flight_data.get("flight_type", "direct"),
                origin_airport=flight_data.get("origin_airport", ""),
                destination_airport=flight_data.get("destination_airport", "FLN"),
                return_airport=flight_data.get("return_airport", ""),
                duration_minutes=flight_data.get("duration_minutes"),
                availability=flight_data.get("availability"),
                luggage_included=flight_data.get("luggage_included", False),
                score=flight_data.get("score"),
                url=flight_data.get("url", ""),
                departure_date=flight_data.get("outbound_departure", "")[:10] if flight_data.get("outbound_departure") else None,
                return_date=flight_data.get("return_departure", "")[:10] if flight_data.get("return_departure") else None,
            )
            
            # Guardar airlines como JSON
            airlines = flight_data.get("airlines", [])
            flight.airlines = airlines
            
            # Parsear search_timestamp si viene como string
            ts = flight_data.get("search_timestamp")
            if isinstance(ts, str):
                try:
                    flight.search_timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    flight.search_timestamp = datetime.utcnow()
            
            session.add(flight)
            session.flush()  # Para obtener el ID
            
            # Registrar en histórico de precios
            if flight.price_usd or flight.price_ars:
                history = PriceHistory(
                    flight_id=flight.id,
                    price_usd=flight.price_usd,
                    price_ars=flight.price_ars,
                )
                session.add(history)
            
            session.commit()
            
            logger.debug(
                f"💾 Vuelo guardado (ID: {flight.id}): "
                f"{', '.join(airlines)} | USD ${flight.price_usd or 'N/D'}"
            )
            
            return flight.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error guardando vuelo: {e}")
            return None
        finally:
            session.close()
    
    def get_recent_flights(self, hours: int = 24) -> list[dict]:
        """
        Obtiene los vuelos encontrados en las últimas N horas.
        
        Args:
            hours: Ventana de tiempo en horas (default: 24)
        
        Returns:
            list[dict]: Lista de vuelos como diccionarios
        """
        session = self._get_session()
        
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            flights = (
                session.query(Flight)
                .filter(Flight.search_timestamp >= since)
                .order_by(desc(Flight.search_timestamp))
                .all()
            )
            
            return [self._flight_to_dict(f) for f in flights]
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo vuelos recientes: {e}")
            return []
        finally:
            session.close()
    
    def get_best_flights(self, limit: int = 10) -> list[dict]:
        """
        Obtiene los mejores vuelos por score.
        
        Args:
            limit: Cantidad máxima de resultados
        
        Returns:
            list[dict]: Lista de vuelos ordenados por score (descendente)
        """
        session = self._get_session()
        
        try:
            flights = (
                session.query(Flight)
                .filter(Flight.score.isnot(None))
                .order_by(desc(Flight.score))
                .limit(limit)
                .all()
            )
            
            return [self._flight_to_dict(f) for f in flights]
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo mejores vuelos: {e}")
            return []
        finally:
            session.close()
    
    def get_previous_price(
        self,
        platform: str,
        airlines: list[str],
        departure_date: str,
    ) -> Optional[float]:
        """
        Obtiene el precio anterior de un vuelo similar para detectar
        caídas/subidas de precio.
        
        Busca el registro más reciente con la misma plataforma,
        aerolíneas y fecha de salida.
        
        Args:
            platform: Nombre de la plataforma
            airlines: Lista de aerolíneas
            departure_date: Fecha de ida (YYYY-MM-DD)
        
        Returns:
            float o None: Precio USD anterior, o None si no hay historial
        """
        session = self._get_session()
        
        try:
            # Buscar vuelo similar más reciente
            airlines_json = json.dumps(airlines) if isinstance(airlines, list) else str(airlines)
            
            flight = (
                session.query(Flight)
                .filter(
                    Flight.platform == platform,
                    Flight.airlines_json == airlines_json,
                    Flight.departure_date == departure_date,
                )
                .order_by(desc(Flight.search_timestamp))
                .first()
            )
            
            if flight:
                return flight.price_usd
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando precio anterior: {e}")
            return None
        finally:
            session.close()
    
    # ====================================================================
    # OPERACIONES CON ALERTAS
    # ====================================================================
    
    def save_alert(
        self,
        flight_id: int,
        alert_type: str,
        telegram_message_id: int = None,
        message_preview: str = None,
    ):
        """
        Registra una alerta enviada por Telegram.
        
        Args:
            flight_id: ID del vuelo que disparó la alerta
            alert_type: Tipo de alerta ("critical", "important", "info", etc.)
            telegram_message_id: ID del mensaje en Telegram
            message_preview: Resumen del contenido del mensaje
        """
        session = self._get_session()
        
        try:
            alert = AlertSent(
                flight_id=flight_id,
                alert_type=alert_type,
                telegram_message_id=telegram_message_id,
                message_preview=message_preview[:200] if message_preview else None,
            )
            session.add(alert)
            session.commit()
            
            logger.debug(f"📱 Alerta registrada: tipo={alert_type}, flight_id={flight_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error registrando alerta: {e}")
        finally:
            session.close()
    
    def was_alert_sent_recently(
        self,
        flight_id: int,
        alert_type: str,
        hours: int = 6,
    ) -> bool:
        """
        Verifica si ya se envió una alerta similar en las últimas N horas.
        Evita enviar alertas duplicadas.
        
        Args:
            flight_id: ID del vuelo
            alert_type: Tipo de alerta
            hours: Ventana de tiempo en horas
        
        Returns:
            bool: True si ya se envió una alerta similar
        """
        session = self._get_session()
        
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            count = (
                session.query(AlertSent)
                .filter(
                    AlertSent.flight_id == flight_id,
                    AlertSent.alert_type == alert_type,
                    AlertSent.sent_at >= since,
                )
                .count()
            )
            
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Error verificando alertas previas: {e}")
            return False  # Ante la duda, permitir enviar
        finally:
            session.close()
    
    # ====================================================================
    # ESTADÍSTICAS Y TENDENCIAS
    # ====================================================================
    
    def get_price_stats(self, hours: int = 24) -> dict:
        """
        Calcula estadísticas de precios para las últimas N horas.
        
        Args:
            hours: Ventana de tiempo en horas
        
        Returns:
            dict: Estadísticas (min, max, avg, count)
        """
        session = self._get_session()
        
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            result = (
                session.query(
                    func.min(Flight.price_usd).label("min_price"),
                    func.max(Flight.price_usd).label("max_price"),
                    func.avg(Flight.price_usd).label("avg_price"),
                    func.count(Flight.id).label("total_flights"),
                )
                .filter(
                    Flight.search_timestamp >= since,
                    Flight.price_usd.isnot(None),
                )
                .one()
            )
            
            return {
                "min_price_usd": result.min_price,
                "max_price_usd": result.max_price,
                "avg_price_usd": round(result.avg_price, 2) if result.avg_price else None,
                "total_flights": result.total_flights,
                "period_hours": hours,
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
        finally:
            session.close()
    
    # ====================================================================
    # MANTENIMIENTO
    # ====================================================================
    
    def cleanup_old_records(self, days: int = None):
        """
        Elimina registros más viejos que N días para mantener la BD pequeña.
        
        Args:
            days: Cantidad de días (default: config DB_CLEANUP_DAYS = 30)
        """
        days = days or DB_CLEANUP_DAYS
        session = self._get_session()
        
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Contar registros a eliminar
            count = (
                session.query(Flight)
                .filter(Flight.created_at < cutoff)
                .count()
            )
            
            if count > 0:
                # Eliminar (cascade borrará price_history y alerts_sent)
                session.query(Flight).filter(Flight.created_at < cutoff).delete()
                session.commit()
                logger.info(f"🧹 Limpieza: {count} vuelo(s) eliminado(s) (>{days} días)")
            else:
                logger.debug(f"🧹 Sin registros viejos para limpiar")
                
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error en limpieza: {e}")
        finally:
            session.close()
    
    # ====================================================================
    # UTILIDADES
    # ====================================================================
    
    def _flight_to_dict(self, flight: Flight) -> dict:
        """
        Convierte un objeto Flight de SQLAlchemy a diccionario.
        
        Args:
            flight: Objeto Flight
        
        Returns:
            dict: Diccionario con todos los datos del vuelo
        """
        return {
            "id": flight.id,
            "platform": flight.platform,
            "airlines": flight.airlines,
            "price_usd": flight.price_usd,
            "price_ars": flight.price_ars,
            "outbound_departure": flight.outbound_departure,
            "outbound_arrival": flight.outbound_arrival,
            "return_departure": flight.return_departure,
            "return_arrival": flight.return_arrival,
            "flight_type": flight.flight_type,
            "origin_airport": flight.origin_airport,
            "destination_airport": flight.destination_airport,
            "return_airport": flight.return_airport,
            "duration_minutes": flight.duration_minutes,
            "availability": flight.availability,
            "luggage_included": flight.luggage_included,
            "score": flight.score,
            "url": flight.url,
            "departure_date": flight.departure_date,
            "return_date": flight.return_date,
            "search_timestamp": flight.search_timestamp.isoformat() if flight.search_timestamp else None,
            "created_at": flight.created_at.isoformat() if flight.created_at else None,
        }


# Ejecutar directamente para inicializar la BD
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestor de base de datos")
    parser.add_argument("--init", action="store_true", help="Inicializar base de datos")
    parser.add_argument("--cleanup", action="store_true", help="Limpiar registros viejos")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    db = DatabaseManager()
    
    if args.init:
        print("✅ Base de datos inicializada correctamente")
    
    if args.cleanup:
        db.cleanup_old_records()
    
    if args.stats:
        stats = db.get_price_stats(hours=168)  # Última semana
        print(f"📊 Estadísticas (última semana):")
        for key, value in stats.items():
            print(f"   {key}: {value}")
