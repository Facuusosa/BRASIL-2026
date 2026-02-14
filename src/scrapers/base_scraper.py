"""
base_scraper.py - Clase base abstracta para todos los scrapers

Define la interfaz que deben seguir todos los scrapers del proyecto.
Cada plataforma (Turismo City, Despegar, etc.) hereda de esta clase
e implementa su lógica específica de scraping.

Incluye funcionalidad común:
- Inicialización de Playwright con stealth mode
- Manejo de contexto del navegador (incógnito, headers, user-agent)
- Retry automático con backoff exponencial
- Captura de screenshots en caso de error
- Logging estandarizado

RESTRICCIÓN: Los scrapers SOLO extraen información pública de precios.
NUNCA interactúan con formularios de pago, checkout o login.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import (
    HEADLESS_MODE,
    STEALTH_MODE,
    PAGE_LOAD_TIMEOUT,
    MAX_RETRIES,
    ORIGIN_CITY,
    DESTINATION_CITY,
    DESTINATION_AIRPORT,
    PASSENGERS,
    CACHE_DIR,
)
from src.utils.logger import get_scraper_logger
from src.utils.helpers import (
    get_random_user_agent,
    random_delay,
    now_iso,
)


class BaseScraper(ABC):
    """
    Clase base abstracta para los scrapers de plataformas de vuelos.
    
    Todos los scrapers deben heredar de esta clase e implementar
    los métodos abstractos: _navigate_and_search() y _parse_results().
    
    Uso típico:
        scraper = TurismoCityScraper()
        flights = await scraper.search(
            departure_date="2026-03-09",
            return_date="2026-03-16",
            passengers=2
        )
    """
    
    # Nombre de la plataforma (lo define cada subclase)
    PLATFORM_NAME = "Base"
    BASE_URL = ""
    
    def __init__(self):
        """Inicializa el scraper con su logger y configuración."""
        self.logger = get_scraper_logger(self.PLATFORM_NAME.lower().replace(" ", "_"))
        self.browser = None
        self.context = None
        self.page = None
    
    # ========================================================================
    # MÉTODOS ABSTRACTOS (cada subclase los implementa)
    # ========================================================================
    
    @abstractmethod
    async def _navigate_and_search(
        self,
        departure_date: str,
        return_date: str,
        passengers: int,
    ) -> bool:
        """
        Navega a la plataforma y ejecuta la búsqueda de vuelos.
        
        Args:
            departure_date: Fecha de ida (YYYY-MM-DD)
            return_date: Fecha de vuelta (YYYY-MM-DD)
            passengers: Cantidad de pasajeros
        
        Returns:
            bool: True si la búsqueda se ejecutó correctamente
        """
        pass
    
    @abstractmethod
    async def _parse_results(self) -> list[dict]:
        """
        Parsea los resultados de la búsqueda visibles en la página.
        
        Returns:
            list[dict]: Lista de vuelos encontrados con toda la info extraída
        """
        pass
    
    # ========================================================================
    # MÉTODO PRINCIPAL DE BÚSQUEDA
    # ========================================================================
    
    async def search(
        self,
        departure_date: str,
        return_date: str,
        passengers: int = PASSENGERS,
    ) -> list[dict]:
        """
        Ejecuta una búsqueda completa de vuelos en la plataforma.
        
        Maneja todo el ciclo de vida del navegador:
        1. Abre Playwright con stealth mode
        2. Crea contexto incógnito con user-agent aleatorio
        3. Navega y busca vuelos
        4. Parsea resultados
        5. Cierra todo limpiamente
        
        Incluye retry automático en caso de fallos.
        
        Args:
            departure_date: Fecha de ida (YYYY-MM-DD)
            return_date: Fecha de vuelta (YYYY-MM-DD)
            passengers: Cantidad de pasajeros (default: 2)
        
        Returns:
            list[dict]: Lista de vuelos encontrados (vacía si no hay resultados)
        """
        flights = []
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.info(
                    f"🔍 Búsqueda en {self.PLATFORM_NAME} "
                    f"(intento {attempt}/{MAX_RETRIES})"
                )
                self.logger.info(
                    f"   📅 {departure_date} → {return_date} | 👥 {passengers} pax"
                )
                
                # Inicializar navegador
                await self._init_browser()
                
                # Ejecutar búsqueda
                success = await self._navigate_and_search(
                    departure_date=departure_date,
                    return_date=return_date,
                    passengers=passengers,
                )
                
                if not success:
                    self.logger.warning(f"⚠️ Búsqueda no completada (intento {attempt})")
                    if attempt < MAX_RETRIES:
                        wait_time = attempt * 10  # Backoff: 10s, 20s, 30s...
                        self.logger.info(f"   ⏳ Esperando {wait_time}s antes de reintentar...")
                        await asyncio.sleep(wait_time)
                    continue
                
                # Parsear resultados
                flights = await self._parse_results()
                
                # Enriquecer cada vuelo con metadatos
                for flight in flights:
                    flight["platform"] = self.PLATFORM_NAME
                    flight["search_timestamp"] = now_iso()
                    if "passengers" not in flight:
                        flight["passengers"] = passengers
                
                self.logger.info(
                    f"✅ {len(flights)} vuelo(s) extraído(s) de {self.PLATFORM_NAME}"
                )
                
                # Búsqueda exitosa, salir del loop de reintentos
                break
                
            except Exception as e:
                self.logger.error(
                    f"❌ Error en intento {attempt}/{MAX_RETRIES}: {e}",
                    exc_info=True,
                )
                
                # Capturar screenshot del error
                await self._capture_error_screenshot(f"error_attempt_{attempt}")
                
                if attempt < MAX_RETRIES:
                    wait_time = attempt * 15
                    self.logger.info(f"   ⏳ Esperando {wait_time}s antes de reintentar...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(
                        f"💥 Todos los reintentos fallaron para {self.PLATFORM_NAME}"
                    )
            
            finally:
                # SIEMPRE cerrar el navegador, incluso si hay error
                await self._close_browser()
        
        return flights
    
    # ========================================================================
    # GESTIÓN DEL NAVEGADOR
    # ========================================================================
    
    async def _init_browser(self):
        """
        Inicializa Playwright con Chromium, stealth mode y contexto incógnito.
        """
        from playwright.async_api import async_playwright
        
        self.logger.debug("🌐 Inicializando navegador...")
        
        self._playwright = await async_playwright().start()
        
        # Lanzar Chromium en modo headless
        self.browser = await self._playwright.chromium.launch(
            headless=HEADLESS_MODE,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        # Crear contexto con user-agent aleatorio (simula usuario real)
        user_agent = get_random_user_agent()
        self.logger.debug(f"   User-Agent: {user_agent[:50]}...")
        
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="es-AR",
            timezone_id="America/Argentina/Buenos_Aires",
            # Permisos mínimos (no necesitamos geolocation, camera, etc.)
            permissions=[],
            # Headers extra para parecer un usuario real
            extra_http_headers={
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "DNT": "1",
            }
        )
        
        # Aplicar stealth mode si está habilitado
        if STEALTH_MODE:
            try:
                # playwright-stealth v2.x
                from playwright_stealth import Stealth
                self.page = await self.context.new_page()
                stealth = Stealth()
                await stealth.apply_stealth(self.page)
                self.logger.debug("   🥷 Stealth mode aplicado (v2)")
            except (ImportError, AttributeError):
                try:
                    # playwright-stealth v1.x (fallback)
                    from playwright_stealth import stealth_async
                    self.page = await self.context.new_page()
                    await stealth_async(self.page)
                    self.logger.debug("   🥷 Stealth mode aplicado (v1)")
                except ImportError:
                    self.logger.warning(
                        "⚠️ playwright-stealth no instalado. Usando modo normal."
                    )
                    self.page = await self.context.new_page()
        else:
            self.page = await self.context.new_page()
        
        # Configurar timeout por defecto
        self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)
        self.page.set_default_navigation_timeout(PAGE_LOAD_TIMEOUT)
        
        self.logger.debug("   ✅ Navegador listo")
    
    async def _close_browser(self):
        """
        Cierra el navegador y libera recursos de forma segura.
        """
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, '_playwright') and self._playwright:
                await self._playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            
            self.logger.debug("🔒 Navegador cerrado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error cerrando navegador: {e}")
    
    # ========================================================================
    # UTILIDADES DE SCRAPING
    # ========================================================================
    
    async def _wait_for_results(
        self,
        selector: str,
        timeout: int = PAGE_LOAD_TIMEOUT,
    ) -> bool:
        """
        Espera a que los resultados de búsqueda aparezcan en la página.
        
        Args:
            selector: Selector CSS de los resultados
            timeout: Timeout en milisegundos
        
        Returns:
            bool: True si los resultados aparecieron
        """
        try:
            self.logger.debug(f"   ⏳ Esperando resultados ({selector})...")
            await self.page.wait_for_selector(selector, timeout=timeout)
            self.logger.debug(f"   ✅ Resultados cargados")
            return True
        except Exception:
            self.logger.warning(f"   ⏰ Timeout esperando resultados ({timeout}ms)")
            return False
    
    async def _safe_text(
        self,
        selector: str,
        default: str = "",
    ) -> str:
        """
        Extrae texto de un elemento de forma segura (sin explotar si no existe).
        
        Args:
            selector: Selector CSS del elemento
            default: Valor por defecto si el elemento no existe
        
        Returns:
            str: Texto del elemento o valor por defecto
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else default
            return default
        except Exception:
            return default
    
    async def _safe_attribute(
        self,
        selector: str,
        attribute: str,
        default: str = "",
    ) -> str:
        """
        Extrae un atributo de un elemento de forma segura.
        
        Args:
            selector: Selector CSS del elemento
            attribute: Nombre del atributo (ej: "href", "data-price")
            default: Valor por defecto
        
        Returns:
            str: Valor del atributo o default
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return value if value else default
            return default
        except Exception:
            return default
    
    async def _capture_error_screenshot(self, label: str = "error"):
        """
        Captura un screenshot de la página actual para debugging.
        Se guarda en data/cache/ con timestamp.
        
        Args:
            label: Etiqueta para el nombre del archivo
        """
        try:
            if self.page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                platform = self.PLATFORM_NAME.lower().replace(" ", "_")
                filename = f"{platform}_{label}_{timestamp}.png"
                filepath = CACHE_DIR / filename
                
                await self.page.screenshot(path=str(filepath), full_page=True)
                self.logger.info(f"📸 Screenshot guardado: {filepath}")
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo capturar screenshot: {e}")
    
    async def _scroll_to_load_more(self, max_scrolls: int = 3):
        """
        Hace scroll hacia abajo para cargar más resultados (lazy loading).
        
        Args:
            max_scrolls: Cantidad máxima de scrolls a realizar
        """
        for i in range(max_scrolls):
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)  # Esperar a que carguen los resultados
            self.logger.debug(f"   📜 Scroll {i+1}/{max_scrolls}")
    
    async def _human_like_typing(self, selector: str, text: str, delay: int = 100):
        """
        Escribe texto en un campo de forma humana (con delays entre caracteres).
        Esto ayuda a evitar detección anti-bot.
        
        Args:
            selector: Selector CSS del campo de texto
            text: Texto a escribir
            delay: Delay entre caracteres en milisegundos
        """
        element = await self.page.wait_for_selector(selector)
        if element:
            # Limpiar el campo primero
            await element.click()
            await self.page.keyboard.press("Control+a")
            await self.page.keyboard.press("Backspace")
            
            # Escribir carácter por carácter con delay aleatorio
            for char in text:
                await element.type(char, delay=random.randint(50, delay))
                await asyncio.sleep(random.uniform(0.05, 0.15))
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} platform='{self.PLATFORM_NAME}'>"
