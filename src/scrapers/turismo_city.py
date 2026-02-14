"""
turismo_city.py - Scraper para Turismo City (turismocity.com.ar)

⭐ PRIORIDAD CRÍTICA - Mejores precios encontrados (30-40% menos que Despegar)

Datos del research:
- Flybondi x2: USD $484 (2 personas con equipaje) 🏆
- Flybondi + JetSmart: USD $537
- Funciona perfectamente en modo incógnito ✅
- Precios mostrados en USD con equipaje incluido

Proceso de búsqueda:
1. Navegar a turismocity.com.ar
2. Ingresar origen: Buenos Aires
3. Ingresar destino: Florianópolis
4. Seleccionar fechas ida y vuelta
5. Seleccionar cantidad de pasajeros
6. Hacer clic en "Buscar"
7. Esperar resultados (10-20 segundos)
8. Parsear cada resultado visible

RESTRICCIÓN: Este scraper SOLO extrae precios públicos.
NUNCA interactúa con formularios de pago o checkout.
"""

import asyncio
import random
import re
from datetime import datetime
from typing import Optional

from src.scrapers.base_scraper import BaseScraper
from src.config import ORIGIN_CITY, DESTINATION_CITY, DESTINATION_AIRPORT


class TurismoCityScraper(BaseScraper):
    """
    Scraper para Turismo City (turismocity.com.ar).
    
    Turismo City es un metabuscador argentino que compara precios
    de múltiples aerolíneas y agencias. Según el research manual,
    ofrece los mejores precios (30-40% menos que Despegar).
    
    Uso:
        scraper = TurismoCityScraper()
        flights = await scraper.search(
            departure_date="2026-03-09",
            return_date="2026-03-16",
            passengers=2
        )
    """
    
    PLATFORM_NAME = "Turismo City"
    BASE_URL = "https://www.turismocity.com.ar"
    
    # ====================================================================
    # SELECTORES CSS (pueden cambiar si Turismo City modifica su web)
    # ====================================================================
    # ⚠️ IMPORTANTE: Actualizar estos selectores si el scraper falla.
    # Tomar un screenshot (se guarda automáticamente) y analizar la página.
    
    SELECTORS = {
        # --- Formulario de búsqueda ---
        "origin_input": 'input[placeholder*="origen"], input[name*="origin"], #origin',
        "destination_input": 'input[placeholder*="destino"], input[name*="destination"], #destination',
        "departure_date": 'input[name*="departure"], input[placeholder*="Ida"]',
        "return_date": 'input[name*="return"], input[placeholder*="Vuelta"]',
        "passengers_selector": '.passengers, .pax-selector, [data-testid="passengers"]',
        "search_button": 'button[type="submit"], .search-button, .btn-search',
        
        # --- Resultados ---
        "results_container": '.results, .flight-results, [data-testid="results"]',
        "result_card": '.result-card, .flight-card, .itinerary',
        "airline_name": '.airline-name, .carrier-name, .airline',
        "price_total": '.price, .total-price, .fare-price',
        "departure_time": '.departure-time, .time-departure',
        "arrival_time": '.arrival-time, .time-arrival',
        "duration": '.duration, .flight-duration',
        "stops": '.stops, .flight-stops, .scales',
        "airport_code": '.airport-code, .iata-code',
        "availability": '.availability, .seats-left, .urgency',
        "book_url": 'a.buy-button, a.book-link, a[href*="redirect"]',
        
        # --- Loading ---
        "loading_indicator": '.loading, .spinner, .searching',
        "no_results": '.no-results, .empty-results',
    }
    
    async def _navigate_and_search(
        self,
        departure_date: str,
        return_date: str,
        passengers: int,
    ) -> bool:
        """
        Navega a Turismo City y ejecuta la búsqueda de vuelos
        usando el formulario interactivo de búsqueda.
        
        Turismo City NO tiene URLs de búsqueda directa (da 404).
        Requiere interactuar con el formulario JavaScript.
        
        Args:
            departure_date: Fecha de ida (YYYY-MM-DD)
            return_date: Fecha de vuelta (YYYY-MM-DD)
            passengers: Cantidad de pasajeros
        
        Returns:
            bool: True si la búsqueda se completó exitosamente
        """
        self.logger.info(f"🌐 Navegando a {self.BASE_URL}...")
        
        try:
            # 1. Navegar a la página principal
            await self.page.goto(self.BASE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Esperar carga de JS
            self.logger.info("   ✅ Página principal cargada")
            
            # 2. Asegurarse de estar en la sección de VUELOS
            try:
                vuelos_tab = await self.page.query_selector(
                    'a[href*="vuelos"], button:has-text("Vuelos"), '
                    '.tab-flights, [data-tab="flights"], '
                    'a:has-text("VUELOS"), a:has-text("Vuelos")'
                )
                if vuelos_tab:
                    await vuelos_tab.click()
                    await asyncio.sleep(1)
                    self.logger.debug("   ✈️ Tab de Vuelos seleccionado")
            except Exception:
                pass  # Si no hay tabs, ya estamos en vuelos
            
            # 3. Completar ORIGEN: Buenos Aires
            self.logger.info("   📝 Completando formulario de búsqueda...")
            origin_filled = await self._fill_autocomplete_field(
                field_selectors=[
                    'input[placeholder*="origen"]', 'input[placeholder*="Origen"]',
                    'input[placeholder*="salida"]', 'input[placeholder*="Salida"]',
                    'input[placeholder*="dónde sal"]', 'input[placeholder*="Donde sal"]',
                    'input[name*="origin"]', '#origin', 
                    'input[data-testid*="origin"]',
                    '.search-form input:first-of-type',
                ],
                text_to_type="Buenos Aires",
                text_to_match="Buenos Aires",
            )
            if not origin_filled:
                self.logger.warning("   ⚠️ No se pudo completar el origen")
                await self._capture_error_screenshot("origin_field_error")
                return False
            
            await asyncio.sleep(1)
            
            # 4. Completar DESTINO: Florianópolis
            dest_filled = await self._fill_autocomplete_field(
                field_selectors=[
                    'input[placeholder*="destino"]', 'input[placeholder*="Destino"]',
                    'input[placeholder*="llegada"]', 'input[placeholder*="Llegada"]',
                    'input[placeholder*="dónde va"]', 'input[placeholder*="Donde va"]',
                    'input[name*="destination"]', '#destination',
                    'input[data-testid*="destination"]',
                ],
                text_to_type="Florianopolis",
                text_to_match="Florianópolis",
            )
            if not dest_filled:
                self.logger.warning("   ⚠️ No se pudo completar el destino")
                await self._capture_error_screenshot("destination_field_error")
                return False
            
            await asyncio.sleep(1)
            
            # 5. Seleccionar fechas
            dates_set = await self._set_dates(departure_date, return_date)
            if not dates_set:
                self.logger.warning("   ⚠️ No se pudieron setear las fechas")
                await self._capture_error_screenshot("dates_error")
                return False
            
            await asyncio.sleep(1)
            
            # 6. Hacer clic en BUSCAR
            search_clicked = await self._click_search_button()
            if not search_clicked:
                self.logger.warning("   ⚠️ No se pudo hacer clic en buscar")
                await self._capture_error_screenshot("search_button_error")
                return False
            
            # 7. Esperar resultados
            self.logger.info("   ⏳ Esperando resultados (esto puede tardar 15-30 seg)...")
            
            # Esperar que desaparezca el loading
            try:
                await self.page.wait_for_selector(
                    self.SELECTORS["loading_indicator"],
                    state="hidden",
                    timeout=45000
                )
            except Exception:
                pass
            
            # Esperar resultados
            results_appeared = await self._wait_for_results(
                self.SELECTORS["result_card"],
                timeout=45000
            )
            
            if not results_appeared:
                no_results = await self.page.query_selector(self.SELECTORS["no_results"])
                if no_results:
                    self.logger.info("   📭 Sin resultados para estas fechas")
                    return True
                
                self.logger.warning("   ⚠️ Los resultados no aparecieron a tiempo")
                await self._capture_error_screenshot("no_results")
                return False
            
            # Scroll para cargar más
            await self._scroll_to_load_more(max_scrolls=2)
            
            self.logger.info("   ✅ Resultados cargados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Error en navegación: {e}")
            await self._capture_error_screenshot("navigation_error")
            return False
    
    async def _parse_results(self) -> list[dict]:
        """
        Parsea los resultados de búsqueda visibles en la página.
        
        Extrae de cada tarjeta de vuelo:
        - Aerolíneas
        - Precio total en USD
        - Horarios de ida y vuelta
        - Tipo (directo/con escala)
        - Aeropuertos
        - Disponibilidad
        - URL de detalle
        
        Returns:
            list[dict]: Lista de vuelos encontrados
        """
        flights = []
        
        try:
            # Obtener todas las tarjetas de resultados
            cards = await self.page.query_selector_all(self.SELECTORS["result_card"])
            
            if not cards:
                self.logger.info("   📭 No se encontraron tarjetas de vuelos")
                return flights
            
            self.logger.info(f"   📦 Parseando {len(cards)} tarjeta(s) de vuelos...")
            
            for i, card in enumerate(cards):
                try:
                    flight = await self._parse_single_card(card, i + 1)
                    if flight:
                        flights.append(flight)
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Error parseando tarjeta #{i+1}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"   ❌ Error parseando resultados: {e}")
            await self._capture_error_screenshot("parse_error")
        
        return flights
    
    async def _parse_single_card(self, card, index: int) -> Optional[dict]:
        """
        Parsea una única tarjeta de resultado de vuelo.
        
        Args:
            card: Elemento de la tarjeta (Playwright ElementHandle)
            index: Número de la tarjeta (para logging)
        
        Returns:
            dict: Datos del vuelo o None si no se pudo parsear
        """
        try:
            # --- Extraer aerolínea(s) ---
            airline_elements = await card.query_selector_all(self.SELECTORS["airline_name"])
            airlines = []
            for el in airline_elements:
                text = await el.text_content()
                if text and text.strip():
                    airlines.append(text.strip())
            
            if not airlines:
                airlines = ["Desconocida"]
            
            # --- Extraer precio ---
            price_element = await card.query_selector(self.SELECTORS["price_total"])
            price_usd = None
            price_text = ""
            if price_element:
                price_text = await price_element.text_content()
                price_usd = self._extract_price(price_text)
            
            # --- Extraer horarios (ida) ---
            dep_times = await card.query_selector_all(self.SELECTORS["departure_time"])
            arr_times = await card.query_selector_all(self.SELECTORS["arrival_time"])
            
            outbound_departure = await self._safe_text_from_element(
                dep_times[0] if dep_times else None
            )
            outbound_arrival = await self._safe_text_from_element(
                arr_times[0] if arr_times else None
            )
            
            # Horarios de vuelta (segundo par de horarios)
            return_departure = await self._safe_text_from_element(
                dep_times[1] if len(dep_times) > 1 else None
            )
            return_arrival = await self._safe_text_from_element(
                arr_times[1] if len(arr_times) > 1 else None
            )
            
            # --- Extraer tipo de vuelo (directo/escala) ---
            stops_element = await card.query_selector(self.SELECTORS["stops"])
            stops_text = ""
            flight_type = "direct"  # Asumir directo por default
            if stops_element:
                stops_text = await stops_element.text_content()
                if stops_text:
                    stops_text = stops_text.strip().lower()
                    if "escala" in stops_text or "stop" in stops_text:
                        flight_type = "1_stop"
                    elif "escalas" in stops_text or "stops" in stops_text:
                        flight_type = "2+_stops"
            
            # --- Extraer duración ---
            duration_element = await card.query_selector(self.SELECTORS["duration"])
            duration_minutes = None
            if duration_element:
                duration_text = await duration_element.text_content()
                duration_minutes = self._parse_duration(duration_text)
            
            # --- Extraer aeropuertos ---
            airport_elements = await card.query_selector_all(self.SELECTORS["airport_code"])
            origin_airport = ""
            destination_airport = ""
            return_airport = ""
            
            airport_texts = []
            for el in airport_elements:
                text = await el.text_content()
                if text:
                    airport_texts.append(text.strip())
            
            if len(airport_texts) >= 2:
                origin_airport = airport_texts[0]
                destination_airport = airport_texts[1]
            if len(airport_texts) >= 4:
                return_airport = airport_texts[3]  # Aeropuerto de llegada de la vuelta
            
            # --- Extraer disponibilidad ---
            avail_element = await card.query_selector(self.SELECTORS["availability"])
            availability = None
            if avail_element:
                avail_text = await avail_element.text_content()
                if avail_text:
                    availability = avail_text.strip()
            
            # --- Extraer URL ---
            url_element = await card.query_selector(self.SELECTORS["book_url"])
            url = ""
            if url_element:
                url = await url_element.get_attribute("href") or ""
            
            # --- Construir diccionario del vuelo ---
            flight = {
                "platform": self.PLATFORM_NAME,
                "airlines": airlines,
                "price_usd": price_usd,
                "price_ars": None,  # Se calcula después con tipo de cambio
                "outbound_departure": outbound_departure,
                "outbound_arrival": outbound_arrival,
                "return_departure": return_departure,
                "return_arrival": return_arrival,
                "flight_type": flight_type,
                "origin_airport": origin_airport,
                "destination_airport": destination_airport or DESTINATION_AIRPORT,
                "return_airport": return_airport,
                "duration_minutes": duration_minutes,
                "availability": availability,
                "luggage_included": True,  # Turismo City siempre incluye equipaje
                "url": url,
                "raw_price_text": price_text,
            }
            
            self.logger.debug(
                f"   ✈️ #{index}: {' + '.join(airlines)} | "
                f"USD ${price_usd or 'N/D'} | {flight_type}"
            )
            
            return flight
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Error parseando tarjeta #{index}: {e}")
            return None
    
    # ====================================================================
    # UTILIDADES INTERNAS
    # ====================================================================
    
    async def _fill_autocomplete_field(
        self,
        field_selectors: list[str],
        text_to_type: str,
        text_to_match: str,
    ) -> bool:
        """
        Completa un campo de autocompletado (origen o destino).
        Intenta múltiples selectores hasta encontrar el campo.
        
        Args:
            field_selectors: Lista de selectores CSS a intentar
            text_to_type: Texto a escribir en el campo
            text_to_match: Texto a buscar en las sugerencias
        
        Returns:
            bool: True si se completó exitosamente
        """
        # Encontrar el campo
        field = None
        for selector in field_selectors:
            try:
                field = await self.page.query_selector(selector)
                if field:
                    self.logger.debug(f"   📍 Campo encontrado: {selector}")
                    break
            except Exception:
                continue
        
        if not field:
            # Intentar buscar cualquier input visible de texto
            all_inputs = await self.page.query_selector_all('input[type="text"], input:not([type])')
            for inp in all_inputs:
                is_visible = await inp.is_visible()
                if is_visible:
                    field = inp
                    self.logger.debug("   📍 Campo encontrado por búsqueda genérica")
                    break
        
        if not field:
            return False
        
        try:
            # Limpiar y hacer clic en el campo
            await field.click()
            await asyncio.sleep(0.5)
            
            # Limpiar campo existente
            await self.page.keyboard.press("Control+a")
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(0.3)
            
            # Escribir letra por letra (simular humano)
            for char in text_to_type:
                await self.page.keyboard.type(char, delay=random.randint(50, 150))
            
            # Esperar sugerencias del autocompletado
            await asyncio.sleep(2)
            
            # Buscar en listas de sugerencias
            suggestion_selectors = [
                'li[role="option"]', '.suggestion', '.autocomplete-item',
                '.autocomplete-result', '.search-suggestion',
                '.dropdown-item', '.list-item', '.option',
                'ul.results li', '.suggestions li', '.pac-item',
            ]
            
            for sel in suggestion_selectors:
                try:
                    suggestions = await self.page.query_selector_all(sel)
                    for suggestion in suggestions:
                        text = await suggestion.text_content()
                        if text and text_to_match.lower() in text.lower():
                            await suggestion.click()
                            self.logger.info(f"   ✅ Seleccionado: {text.strip()[:50]}")
                            return True
                except Exception:
                    continue
            
            # Si no encontró sugerencia exacta, hacer click en primera opción visible
            for sel in suggestion_selectors:
                try:
                    first = await self.page.query_selector(sel)
                    if first and await first.is_visible():
                        await first.click()
                        text = await first.text_content()
                        self.logger.info(f"   ✅ Seleccionada primera opción: {(text or '').strip()[:50]}")
                        return True
                except Exception:
                    continue
            
            # Último recurso: presionar Enter
            await self.page.keyboard.press("Enter")
            self.logger.debug("   ℹ️ Sin sugerencias, presionando Enter")
            return True
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Error completando campo: {e}")
            return False
    
    async def _set_dates(self, departure_date: str, return_date: str) -> bool:
        """
        Configura las fechas de ida y vuelta en el formulario.
        Intenta interactuar con el date picker del sitio.
        
        Args:
            departure_date: Fecha de ida (YYYY-MM-DD)
            return_date: Fecha de vuelta (YYYY-MM-DD)
        
        Returns:
            bool: True si se configuraron las fechas
        """
        try:
            dep = datetime.strptime(departure_date, "%Y-%m-%d")
            ret = datetime.strptime(return_date, "%Y-%m-%d")
            
            # Intentar encontrar campos de fecha
            date_selectors = [
                'input[name*="departure"]', 'input[name*="salida"]',
                'input[placeholder*="Ida"]', 'input[placeholder*="ida"]',
                'input[placeholder*="Salida"]', 'input[type="date"]',
                'input[data-testid*="departure"]', 'input[data-testid*="date"]',
                '.date-input', '.departure-date',
            ]
            
            departure_field = None
            for sel in date_selectors:
                departure_field = await self.page.query_selector(sel)
                if departure_field:
                    break
            
            if departure_field:
                # Si es input type=date, setear valor directamente
                input_type = await departure_field.get_attribute("type")
                if input_type == "date":
                    await departure_field.fill(departure_date)
                    self.logger.info(f"   📅 Fecha ida: {departure_date}")
                else:
                    await departure_field.click()
                    await asyncio.sleep(1)
                    
                    # Intentar navegar el calendario
                    success = await self._select_calendar_date(dep)
                    if not success:
                        # Fallback: escribir la fecha
                        await self.page.keyboard.press("Control+a")
                        date_str = dep.strftime("%d/%m/%Y")
                        await self.page.keyboard.type(date_str, delay=50)
                        await self.page.keyboard.press("Enter")
                    
                    self.logger.info(f"   📅 Fecha ida: {departure_date}")
            else:
                self.logger.warning("   ⚠️ Campo de fecha de ida no encontrado")
                # Intentar buscar cualquier elemento clickeable de fechas
                date_area = await self.page.query_selector(
                    '.dates, .date-picker-trigger, [data-testid*="date"]'
                )
                if date_area:
                    await date_area.click()
                    await asyncio.sleep(1)
            
            await asyncio.sleep(1)
            
            # Fecha de vuelta
            return_selectors = [
                'input[name*="return"]', 'input[name*="regreso"]',
                'input[placeholder*="Vuelta"]', 'input[placeholder*="vuelta"]',
                'input[placeholder*="Regreso"]',
                'input[data-testid*="return"]',
                '.return-date',
            ]
            
            return_field = None
            for sel in return_selectors:
                return_field = await self.page.query_selector(sel)
                if return_field:
                    break
            
            if return_field:
                input_type = await return_field.get_attribute("type")
                if input_type == "date":
                    await return_field.fill(return_date)
                else:
                    await return_field.click()
                    await asyncio.sleep(1)
                    success = await self._select_calendar_date(ret)
                    if not success:
                        await self.page.keyboard.press("Control+a")
                        date_str = ret.strftime("%d/%m/%Y")
                        await self.page.keyboard.type(date_str, delay=50)
                        await self.page.keyboard.press("Enter")
                
                self.logger.info(f"   📅 Fecha vuelta: {return_date}")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"   ⚠️ Error seteando fechas: {e}")
            return True  # Continuar de todas formas
    
    async def _select_calendar_date(self, target_date: datetime) -> bool:
        """
        Intenta seleccionar una fecha en un calendario visual.
        
        Args:
            target_date: Fecha a seleccionar
        
        Returns:
            bool: True si se seleccionó la fecha
        """
        try:
            day = target_date.day
            
            # Buscar el día en el calendario visible
            day_selectors = [
                f'td[data-day="{day}"]',
                f'button:has-text("{day}")',
                f'.calendar-day:has-text("{day}")',
                f'[data-date*="{target_date.strftime("%Y-%m-%d")}"]',
            ]
            
            for sel in day_selectors:
                try:
                    day_element = await self.page.query_selector(sel)
                    if day_element and await day_element.is_visible():
                        await day_element.click()
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception:
            return False
    
    async def _click_search_button(self) -> bool:
        """
        Encuentra y hace clic en el botón de búsqueda.
        Intenta múltiples selectores.
        
        Returns:
            bool: True si se hizo clic exitosamente
        """
        button_selectors = [
            'button[type="submit"]',
            '.search-button', '.btn-search',
            'button:has-text("Buscar")', 'button:has-text("BUSCAR")',
            'a:has-text("Buscar")', 'a:has-text("BUSCAR")',
            'input[type="submit"]',
            '.search-form button',
            '[data-testid*="search"]',
        ]
        
        for sel in button_selectors:
            try:
                button = await self.page.query_selector(sel)
                if button and await button.is_visible():
                    await button.click()
                    self.logger.info("   🔍 Búsqueda iniciada")
                    return True
            except Exception:
                continue
        
        # Último recurso: presionar Enter
        try:
            await self.page.keyboard.press("Enter")
            self.logger.info("   🔍 Búsqueda iniciada (Enter)")
            return True
        except Exception:
            self.logger.warning("   ⚠️ Botón de búsqueda no encontrado")
            return False
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """
        Extrae el precio numérico de un texto de precio.
        
        Maneja formatos como:
        - "USD 484"
        - "US$ 484"
        - "$484"
        - "484.00"
        - "1.204.500"  (formato argentino con puntos)
        
        Args:
            price_text: Texto con el precio
        
        Returns:
            float o None: Precio extraído o None si no se pudo parsear
        """
        if not price_text:
            return None
        
        try:
            # Limpiar el texto
            text = price_text.strip()
            
            # Remover símbolos de moneda
            text = text.replace("USD", "").replace("US$", "").replace("$", "")
            text = text.replace("ARS", "").strip()
            
            # Detectar si es formato argentino (punto como separador de miles)
            # Formato argentino: 1.234.567 o 1.234.567,89
            if "." in text and "," in text:
                # Formato mixto: 1.234,56
                text = text.replace(".", "").replace(",", ".")
            elif text.count(".") > 1:
                # Múltiples puntos: 1.234.567 (formato argentino)
                text = text.replace(".", "")
            elif "," in text:
                # Coma como decimal: 484,50
                text = text.replace(",", ".")
            
            # Extraer solo números y punto decimal
            numbers = re.findall(r"[\d.]+", text)
            if numbers:
                return float(numbers[0])
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def _parse_duration(self, duration_text: str) -> Optional[int]:
        """
        Parsea un texto de duración a minutos totales.
        
        Maneja formatos como:
        - "1h 55min"
        - "2h 05m"
        - "1:55"
        - "115 min"
        
        Args:
            duration_text: Texto con la duración
        
        Returns:
            int o None: Duración en minutos o None
        """
        if not duration_text:
            return None
        
        try:
            text = duration_text.strip().lower()
            
            # Formato "Xh YYmin" o "Xh YYm"
            match = re.search(r"(\d+)\s*h\s*(\d+)", text)
            if match:
                hours = int(match.group(1))
                mins = int(match.group(2))
                return hours * 60 + mins
            
            # Formato "H:MM"
            match = re.search(r"(\d+):(\d+)", text)
            if match:
                hours = int(match.group(1))
                mins = int(match.group(2))
                return hours * 60 + mins
            
            # Formato "XXX min"
            match = re.search(r"(\d+)\s*min", text)
            if match:
                return int(match.group(1))
            
            return None
            
        except (ValueError, AttributeError):
            return None
    
    async def _safe_text_from_element(self, element) -> str:
        """
        Extrae texto de un elemento de forma segura.
        
        Args:
            element: Playwright ElementHandle o None
        
        Returns:
            str: Texto del elemento o string vacío
        """
        if element is None:
            return ""
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception:
            return ""
