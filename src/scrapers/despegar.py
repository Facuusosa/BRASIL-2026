"""
despegar.py - Scraper para Despegar (despegar.com.ar)

🔴 PRIORIDAD CRÍTICA (secundaria después de Turismo City)

Datos del research:
- JetSmart x2: USD $700 (2 personas con equipaje)
- GOL x2: USD $767
- Precios finales CON equipaje incluido
- Funciona en modo incógnito ✅
- Mayor variedad de aerolíneas que Turismo City

Proceso de búsqueda:
1. Navegar a despegar.com.ar/vuelos/
2. Buscar "Buenos Aires" → "Florianópolis"
3. Seleccionar fechas
4. Ejecutar búsqueda
5. Parsear resultados

RESTRICCIÓN: Este scraper SOLO extrae precios públicos.
NUNCA interactúa con formularios de pago o checkout.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional

from src.scrapers.base_scraper import BaseScraper
from src.config import DESTINATION_AIRPORT


class DespegarScraper(BaseScraper):
    """
    Scraper para Despegar (despegar.com.ar).
    
    Despegar es una agencia de viajes online argentina.
    Muestra precios finales con equipaje incluido.
    
    Uso:
        scraper = DespegarScraper()
        flights = await scraper.search(
            departure_date="2026-03-09",
            return_date="2026-03-16",
            passengers=2
        )
    """
    
    PLATFORM_NAME = "Despegar"
    BASE_URL = "https://www.despegar.com.ar"
    
    # ====================================================================
    # SELECTORES CSS
    # ====================================================================
    
    SELECTORS = {
        # --- Resultados ---
        "results_container": '.results-cluster-container, [data-testid="resultsList"]',
        "result_card": '.cluster, .result-item, [data-testid="resultItem"]',
        "airline_name": '.airline-name, .carrier-name, .airlines-label',
        "price_total": '.price-amount, .fare-price, .cluster-price',
        "currency": '.price-currency, .currency-symbol',
        "departure_time": '.departure, .segment-time-departure',
        "arrival_time": '.arrival, .segment-time-arrival',
        "duration": '.duration, .segment-duration',
        "stops": '.stops-text, .segment-stops',
        "airport_code": '.airport-code, .airport',
        "availability": '.urgency-message, .seats-left',
        
        # --- Loading ---
        "loading_indicator": '.results-loading, .spinner',
        "no_results": '.no-results, .empty-state',
    }
    
    async def _navigate_and_search(
        self,
        departure_date: str,
        return_date: str,
        passengers: int,
    ) -> bool:
        """
        Navega a Despegar y ejecuta la búsqueda de vuelos.
        
        Despegar tiene URLs de búsqueda con formato predecible:
        https://www.despegar.com.ar/vuelos/BUE/FLN/2026-03-09/2026-03-16/2/0/0
        
        Args:
            departure_date: Fecha de ida (YYYY-MM-DD)
            return_date: Fecha de vuelta (YYYY-MM-DD)
            passengers: Cantidad de pasajeros
        
        Returns:
            bool: True si la búsqueda se completó exitosamente
        """
        self.logger.info(f"🌐 Navegando a Despegar...")
        
        try:
            # Construir URL de búsqueda directa
            search_url = self._build_search_url(departure_date, return_date, passengers)
            
            self.logger.info(f"   🔗 URL: {search_url[:80]}...")
            await self.page.goto(search_url, wait_until="domcontentloaded")
            
            # Esperar a que carguen los resultados
            self.logger.info("   ⏳ Esperando resultados...")
            
            # Cerrar posibles popups/modales (Despegar suele mostrar)
            await self._close_popups()
            
            # Esperar que desaparezca el loading
            try:
                await self.page.wait_for_selector(
                    self.SELECTORS["loading_indicator"],
                    state="hidden",
                    timeout=30000
                )
            except Exception:
                pass
            
            # Esperar resultados
            results_appeared = await self._wait_for_results(
                self.SELECTORS["result_card"],
                timeout=30000
            )
            
            if not results_appeared:
                no_results = await self.page.query_selector(self.SELECTORS["no_results"])
                if no_results:
                    self.logger.info("   📭 Despegar: Sin resultados para estas fechas")
                    return True
                
                self.logger.warning("   ⚠️ Los resultados no aparecieron a tiempo")
                await self._capture_error_screenshot("no_results_despegar")
                return False
            
            # Scroll para cargar más
            await self._scroll_to_load_more(max_scrolls=2)
            
            self.logger.info("   ✅ Resultados cargados en Despegar")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Error en navegación a Despegar: {e}")
            await self._capture_error_screenshot("navigation_error_despegar")
            return False
    
    async def _parse_results(self) -> list[dict]:
        """
        Parsea los resultados de búsqueda en Despegar.
        
        Returns:
            list[dict]: Lista de vuelos encontrados
        """
        flights = []
        
        try:
            cards = await self.page.query_selector_all(self.SELECTORS["result_card"])
            
            if not cards:
                self.logger.info("   📭 No se encontraron resultados en Despegar")
                return flights
            
            self.logger.info(f"   📦 Parseando {len(cards)} resultado(s) de Despegar...")
            
            for i, card in enumerate(cards):
                try:
                    flight = await self._parse_single_card(card, i + 1)
                    if flight:
                        flights.append(flight)
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Error parseando resultado #{i+1}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"   ❌ Error en parsing de Despegar: {e}")
            await self._capture_error_screenshot("parse_error_despegar")
        
        return flights
    
    async def _parse_single_card(self, card, index: int) -> Optional[dict]:
        """
        Parsea una tarjeta de resultado individual de Despegar.
        
        Args:
            card: Elemento de la tarjeta
            index: Número de tarjeta (para logging)
        
        Returns:
            dict o None: Datos del vuelo
        """
        try:
            # --- Aerolíneas ---
            airline_els = await card.query_selector_all(self.SELECTORS["airline_name"])
            airlines = []
            for el in airline_els:
                text = await el.text_content()
                if text and text.strip():
                    airlines.append(text.strip())
            if not airlines:
                airlines = ["Desconocida"]
            
            # --- Precio ---
            price_el = await card.query_selector(self.SELECTORS["price_total"])
            price_text = ""
            price_usd = None
            price_ars = None
            
            if price_el:
                price_text = await price_el.text_content()
                
                # Detectar moneda
                currency_el = await card.query_selector(self.SELECTORS["currency"])
                currency = ""
                if currency_el:
                    currency = (await currency_el.text_content() or "").strip()
                
                raw_price = self._extract_price(price_text)
                
                if "USD" in currency or "US" in currency:
                    price_usd = raw_price
                else:
                    price_ars = raw_price
            
            # --- Horarios ---
            dep_times = await card.query_selector_all(self.SELECTORS["departure_time"])
            arr_times = await card.query_selector_all(self.SELECTORS["arrival_time"])
            
            outbound_departure = ""
            outbound_arrival = ""
            return_departure = ""
            return_arrival = ""
            
            if dep_times:
                outbound_departure = await self._safe_el_text(dep_times[0])
            if arr_times:
                outbound_arrival = await self._safe_el_text(arr_times[0])
            if len(dep_times) > 1:
                return_departure = await self._safe_el_text(dep_times[1])
            if len(arr_times) > 1:
                return_arrival = await self._safe_el_text(arr_times[1])
            
            # --- Tipo de vuelo ---
            stops_el = await card.query_selector(self.SELECTORS["stops"])
            flight_type = "direct"
            if stops_el:
                stops_text = (await stops_el.text_content() or "").lower()
                if "escala" in stops_text or "stop" in stops_text:
                    flight_type = "1_stop"
                elif "escalas" in stops_text:
                    flight_type = "2+_stops"
                elif "directo" in stops_text or "nonstop" in stops_text:
                    flight_type = "direct"
            
            # --- Duración ---
            duration_el = await card.query_selector(self.SELECTORS["duration"])
            duration_minutes = None
            if duration_el:
                d_text = await duration_el.text_content()
                duration_minutes = self._parse_duration(d_text)
            
            # --- Aeropuertos ---
            airport_els = await card.query_selector_all(self.SELECTORS["airport_code"])
            airports = []
            for el in airport_els:
                text = await el.text_content()
                if text:
                    airports.append(text.strip())
            
            origin_airport = airports[0] if airports else ""
            return_airport = airports[-1] if len(airports) >= 4 else ""
            
            # --- Disponibilidad ---
            avail_el = await card.query_selector(self.SELECTORS["availability"])
            availability = None
            if avail_el:
                availability = (await avail_el.text_content() or "").strip()
            
            flight = {
                "platform": self.PLATFORM_NAME,
                "airlines": airlines,
                "price_usd": price_usd,
                "price_ars": price_ars,
                "outbound_departure": outbound_departure,
                "outbound_arrival": outbound_arrival,
                "return_departure": return_departure,
                "return_arrival": return_arrival,
                "flight_type": flight_type,
                "origin_airport": origin_airport,
                "destination_airport": DESTINATION_AIRPORT,
                "return_airport": return_airport,
                "duration_minutes": duration_minutes,
                "availability": availability,
                "luggage_included": True,  # Despegar muestra precios finales
                "url": self.page.url,
                "raw_price_text": price_text,
            }
            
            self.logger.debug(
                f"   ✈️ #{index}: {' + '.join(airlines)} | "
                f"{'USD $' + str(price_usd) if price_usd else format_ars(price_ars)} | "
                f"{flight_type}"
            )
            
            return flight
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Error parseando tarjeta Despegar #{index}: {e}")
            return None
    
    # ====================================================================
    # UTILIDADES
    # ====================================================================
    
    def _build_search_url(
        self,
        departure_date: str,
        return_date: str,
        passengers: int,
    ) -> str:
        """
        Construye la URL de búsqueda directa de Despegar.
        
        Formato: /vuelos/BUE/FLN/2026-03-09/2026-03-16/2/0/0
        (2 adultos, 0 niños, 0 infantes)
        """
        return (
            f"{self.BASE_URL}/vuelos/"
            f"BUE/{DESTINATION_AIRPORT}/"
            f"{departure_date}/{return_date}/"
            f"{passengers}/0/0"
        )
    
    async def _close_popups(self):
        """Cierra popups y modales que Despegar suele mostrar."""
        popup_selectors = [
            '.close-button',
            '[data-testid="close-button"]',
            '.modal-close',
            'button[aria-label="Cerrar"]',
            '.cookie-banner button',
        ]
        
        for selector in popup_selectors:
            try:
                popup = await self.page.query_selector(selector)
                if popup:
                    await popup.click()
                    self.logger.debug(f"   🔕 Popup cerrado: {selector}")
                    await asyncio.sleep(0.5)
            except Exception:
                pass
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extrae precio numérico de un texto."""
        if not price_text:
            return None
        
        try:
            text = price_text.strip()
            text = re.sub(r"[^\d.,]", "", text)
            
            if "." in text and "," in text:
                text = text.replace(".", "").replace(",", ".")
            elif text.count(".") > 1:
                text = text.replace(".", "")
            elif "," in text:
                text = text.replace(",", ".")
            
            return float(text) if text else None
        except (ValueError, IndexError):
            return None
    
    def _parse_duration(self, text: str) -> Optional[int]:
        """Parsea texto de duración a minutos totales."""
        if not text:
            return None
        try:
            text = text.strip().lower()
            match = re.search(r"(\d+)\s*h\s*(\d+)", text)
            if match:
                return int(match.group(1)) * 60 + int(match.group(2))
            match = re.search(r"(\d+):(\d+)", text)
            if match:
                return int(match.group(1)) * 60 + int(match.group(2))
            return None
        except (ValueError, AttributeError):
            return None
    
    async def _safe_el_text(self, element) -> str:
        """Extrae texto de un elemento de forma segura."""
        if not element:
            return ""
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception:
            return ""


def format_ars(price):
    """Helper para formatear precio ARS."""
    if price is None:
        return "N/D"
    return f"${int(price):,.0f}".replace(",", ".")
