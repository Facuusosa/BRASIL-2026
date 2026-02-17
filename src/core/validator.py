import os
import sqlite3

class PriceValidator:
    """Valida los precios de Flybondi contra datos históricos para asegurar decisiones correctas."""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(os.getcwd(), "flybondi_monitor.db")
        
    def _connect(self):
        return sqlite3.connect(self.db_path)

    def validate_price(self, route, current_price, date_departure):
        """Devuelve un nivel de confianza (HIGH, MEDIUM, LOW) para el precio actual."""
        # 1. Validación de Rango (Ancla: $700k - $900k)
        # Si el precio es < 500k, es sospechoso (ERROR o GLITCH).
        # Si es > 2M, es sospechoso (ERROR scraping).
        
        confidence = "HIGH"
        
        if current_price < 500000:
            confidence = "LOW (GLITCH?)"
        elif current_price > 2000000:
            confidence = "LOW (ERROR?)"
            
        # 2. Validación Histórica (Comparación con promedio de ayer)
        # En el futuro, consultaríamos la DB para ver el precio de ayer.
        # Por ahora, usamos heurística simple.

        return confidence

    def detect_arbitrage_opportunity(self, current_price, market_average=850000):
        """Calcula el % de descuento real vs promedio de mercado."""
        target_discount = 0.20 # 20%
        
        diff = market_average - current_price
        pct_diff = (diff / market_average)
        
        is_opportunity = pct_diff >= target_discount
        return is_opportunity, pct_diff * 100

if __name__ == "__main__":
    v = PriceValidator()
    print(v.detect_arbitrage_opportunity(637000)) # Test con precio actual
