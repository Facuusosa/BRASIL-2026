"""
scorer.py - Sistema de scoring de vuelos (0-100)

Factores:
- Precio (50%): Más barato = mejor score
- Horario (30%): Diurnos preferidos sobre madrugada
- Aeropuerto (10%): Mismo aeropuerto ida/vuelta = bonus
- Duración (10%): Directo = mejor score
"""

import re
from typing import Optional
from src.config import BASELINE_PRICES, CRITICAL_PRICE_USD
from src.utils.logger import get_analyzer_logger

logger = get_analyzer_logger()


class FlightScorer:
    WEIGHT_PRICE = 0.50
    WEIGHT_SCHEDULE = 0.30
    WEIGHT_AIRPORT = 0.10
    WEIGHT_DURATION = 0.10

    PRICE_BEST = BASELINE_PRICES["best_price_usd"]
    PRICE_CRITICAL = CRITICAL_PRICE_USD
    PRICE_GOOD = BASELINE_PRICES["good_price_usd"]
    PRICE_MAX = BASELINE_PRICES["expensive_price_usd"]

    def calculate_score(self, flight: dict) -> float:
        ps = self._score_price(flight)
        ss = self._score_schedule(flight)
        ap = self._score_airport(flight)
        ds = self._score_duration(flight)
        total = min(100, max(0, ps + ss + ap + ds))
        return round(total, 1)

    def explain_score(self, flight: dict) -> dict:
        ps = self._score_price(flight)
        ss = self._score_schedule(flight)
        ap = self._score_airport(flight)
        ds = self._score_duration(flight)
        total = min(100, max(0, ps + ss + ap + ds))

        if total >= 90:
            label, rec = "🏆 EXCELENTE", "¡Comprar YA!"
        elif total >= 70:
            label, rec = "✅ MUY BUENO", "Considerar comprar"
        elif total >= 50:
            label, rec = "🟡 ACEPTABLE", "Esperar si no hay urgencia"
        elif total >= 30:
            label, rec = "🟠 CARO", "Esperar mejor oferta"
        else:
            label, rec = "🔴 MUY CARO", "No recomendado"

        return {
            "total_score": round(total, 1),
            "label": label,
            "recommendation": rec,
            "breakdown": {
                "price": {"score": round(ps, 1), "max": 50},
                "schedule": {"score": round(ss, 1), "max": 30},
                "airport": {"score": round(ap, 1), "max": 10},
                "duration": {"score": round(ds, 1), "max": 10},
            },
        }

    def _score_price(self, flight: dict) -> float:
        price = flight.get("price_usd")
        if not price or price <= 0:
            price_ars = flight.get("price_ars")
            if price_ars and price_ars > 0:
                rate = BASELINE_PRICES.get("exchange_rate_blue", 1333)
                price = price_ars / rate
            else:
                return 0
        if price <= self.PRICE_CRITICAL:
            return 50.0
        elif price <= self.PRICE_BEST:
            return 45.0
        elif price <= self.PRICE_GOOD:
            ratio = (price - self.PRICE_BEST) / (self.PRICE_GOOD - self.PRICE_BEST)
            return 45.0 - (ratio * 10)
        elif price <= self.PRICE_MAX:
            ratio = (price - self.PRICE_GOOD) / (self.PRICE_MAX - self.PRICE_GOOD)
            return 35.0 - (ratio * 35)
        return 0.0

    def _score_schedule(self, flight: dict) -> float:
        out_h = self._extract_hour(flight.get("outbound_departure", ""))
        ret_h = self._extract_hour(flight.get("return_departure", ""))
        out_m = self._hour_mult(out_h) if out_h is not None else 0.5
        ret_m = self._hour_mult(ret_h) if ret_h is not None else 0.5
        return 30.0 * ((out_m + ret_m) / 2)

    def _score_airport(self, flight: dict) -> float:
        origin = flight.get("origin_airport", "")
        ret = flight.get("return_airport", "")
        if not origin or not ret:
            return 5.0
        return 10.0 if origin == ret else 8.5

    def _score_duration(self, flight: dict) -> float:
        ft = flight.get("flight_type", "direct")
        if ft == "direct":
            return 10.0
        elif ft == "1_stop":
            return 7.0
        elif ft == "2+_stops":
            return 4.0
        dur = flight.get("duration_minutes")
        if dur:
            if dur <= 150:
                return 10.0
            elif dur <= 360:
                return 7.0
            return 4.0
        return 7.0

    def _hour_mult(self, hour: int) -> float:
        if 8 <= hour <= 20:
            return 1.0
        elif 6 <= hour < 8 or 20 < hour <= 22:
            return 0.85
        elif hour >= 22 or 5 <= hour < 6:
            return 0.6
        return 0.4

    def _extract_hour(self, time_str: str) -> Optional[int]:
        if not time_str:
            return None
        try:
            m = re.search(r"(\d{1,2}):(\d{2})", str(time_str))
            if m:
                h = int(m.group(1))
                return h if 0 <= h <= 23 else None
        except (ValueError, AttributeError):
            pass
        return None
