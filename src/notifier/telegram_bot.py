"""
telegram_bot.py - Sistema de notificaciones por Telegram

Envía alertas de precios de vuelos al usuario por Telegram.
Tipos de alerta:
- 🔴 CRÍTICA: Precio muy bajo o disponibilidad crítica
- 🟡 IMPORTANTE: Buen precio detectado
- 📊 REPORTE: Resumen diario de precios
- ❌ ERROR: Errores del bot

Uso:
    from src.notifier.telegram_bot import TelegramNotifier
    notifier = TelegramNotifier()
    await notifier.send_critical_alert(flight)
"""

from datetime import datetime
from typing import Optional
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils.logger import get_notifier_logger
from src.utils.helpers import (
    format_price_ars,
    format_price_usd,
    now_iso,
    time_ago,
    usd_to_ars,
)

logger = get_notifier_logger()


class TelegramNotifier:
    """Bot de Telegram para enviar alertas de precios de vuelos."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self._bot = None

        if not self.token or not self.chat_id:
            logger.warning(
                "⚠️ Telegram no configurado. "
                "Configurá TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env"
            )

    async def _get_bot(self):
        """Inicializa el bot de Telegram (lazy loading)."""
        if self._bot is None:
            try:
                from telegram import Bot
                self._bot = Bot(token=self.token)
                logger.debug("✅ Bot de Telegram inicializado")
            except ImportError:
                logger.error(
                    "❌ python-telegram-bot no instalado. "
                    "Ejecutá: pip install python-telegram-bot"
                )
                raise
        return self._bot

    async def send_message(
        self,
        text: str,
        silent: bool = False,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """
        Envía un mensaje por Telegram.

        Args:
            text: Contenido del mensaje
            silent: Si True, no hace sonido en el teléfono
            parse_mode: Formato del mensaje ("HTML" o "Markdown")

        Returns:
            int: ID del mensaje enviado, o None si falla
        """
        if not self.token or not self.chat_id:
            logger.warning("📱 Telegram no configurado, mensaje no enviado")
            logger.info(f"📝 Mensaje (solo log): {text[:100]}...")
            return None

        try:
            bot = await self._get_bot()
            message = await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_notification=silent,
                disable_web_page_preview=True,
            )
            logger.info(f"📱 Mensaje enviado (ID: {message.message_id})")
            return message.message_id

        except Exception as e:
            logger.error(f"❌ Error enviando mensaje Telegram: {e}")
            return None

    async def send_critical_alert(self, flight: dict) -> Optional[int]:
        """Envía alerta CRÍTICA 🔴 (con sonido)."""
        msg = self._format_critical_alert(flight)
        return await self.send_message(msg, silent=False)

    async def send_important_alert(self, flight: dict) -> Optional[int]:
        """Envía alerta IMPORTANTE 🟡 (silenciosa)."""
        msg = self._format_important_alert(flight)
        return await self.send_message(msg, silent=True)

    async def send_daily_report(self, flights: list[dict]) -> Optional[int]:
        """Envía reporte diario 📊."""
        msg = self._format_daily_report(flights)
        return await self.send_message(msg, silent=True)

    async def send_error_alert(self, error_msg: str) -> Optional[int]:
        """Envía alerta de error ❌."""
        msg = f"❌ <b>ERROR DEL BOT</b>\n\n{error_msg}\n\n⏰ {now_iso()}"
        return await self.send_message(msg, silent=True)

    # ================================================================
    # FORMATEO DE MENSAJES
    # ================================================================

    def _format_critical_alert(self, flight: dict) -> str:
        airlines = self._airlines_str(flight)
        price_usd = flight.get("price_usd")
        price_ars = flight.get("price_ars") or (
            usd_to_ars(price_usd) if price_usd else None
        )
        score = flight.get("score", "N/D")

        out_dep = flight.get("outbound_departure", "?")
        out_arr = flight.get("outbound_arrival", "?")
        ret_dep = flight.get("return_departure", "?")
        ret_arr = flight.get("return_arrival", "?")

        origin = flight.get("origin_airport", "?")
        dest = flight.get("destination_airport", "FLN")
        ret_ap = flight.get("return_airport", "?")

        url = flight.get("url", "")
        platform = flight.get("platform", "?")

        msg = (
            f"🔴 <b>ALERTA CRÍTICA - PRECIO BAJO</b>\n\n"
            f"💰 Precio: <b>{format_price_usd(price_usd)}</b>"
        )
        if price_ars:
            msg += f" ({format_price_ars(price_ars)})"
        msg += (
            f"\n✈️ Aerolíneas: {airlines}\n"
            f"📅 Fechas: 9-16 marzo 2026\n"
            f"🕐 Ida: {out_dep} → {out_arr}\n"
            f"🕐 Vuelta: {ret_dep} → {ret_arr}\n"
            f"🛫 Aeropuertos: {origin} → {dest} → {ret_ap}\n"
            f"💼 Equipaje: 20kg incluido\n\n"
            f"🎯 Score: <b>{score}/100</b>\n"
            f"🌐 Plataforma: {platform}\n"
        )
        if url:
            msg += f"\n🔗 <a href='{url}'>Ver oferta</a>\n"
        msg += f"\n⏰ {now_iso()}"
        return msg

    def _format_important_alert(self, flight: dict) -> str:
        airlines = self._airlines_str(flight)
        price_usd = flight.get("price_usd")
        score = flight.get("score", "N/D")
        platform = flight.get("platform", "?")
        ft = flight.get("flight_type", "?")

        msg = (
            f"🟡 <b>ALERTA IMPORTANTE</b>\n\n"
            f"💰 Precio: <b>{format_price_usd(price_usd)}</b>\n"
            f"✈️ {airlines} ({ft})\n"
            f"🎯 Score: {score}/100\n"
            f"🌐 {platform}\n\n"
            f"⏰ {now_iso()}"
        )
        return msg

    def _format_daily_report(self, flights: list[dict]) -> str:
        if not flights:
            return (
                f"📊 <b>REPORTE DIARIO</b>\n\n"
                f"📭 Sin vuelos encontrados en las últimas 24hs\n"
                f"⏰ {now_iso()}"
            )

        prices = [f.get("price_usd", 0) for f in flights if f.get("price_usd")]
        min_p = min(prices) if prices else 0
        max_p = max(prices) if prices else 0
        avg_p = sum(prices) / len(prices) if prices else 0

        best = min(flights, key=lambda f: f.get("price_usd", 999999))
        best_airlines = self._airlines_str(best)

        msg = (
            f"📊 <b>REPORTE DIARIO - Vuelos BUE→FLN</b>\n\n"
            f"📈 Búsquedas: {len(flights)} vuelo(s)\n"
            f"💰 Mínimo: <b>{format_price_usd(min_p)}</b>\n"
            f"💰 Máximo: {format_price_usd(max_p)}\n"
            f"💰 Promedio: {format_price_usd(avg_p)}\n\n"
            f"🏆 Mejor: {best_airlines} a {format_price_usd(min_p)}\n\n"
            f"⏰ {now_iso()}"
        )
        return msg

    def _airlines_str(self, flight: dict) -> str:
        airlines = flight.get("airlines", ["?"])
        if isinstance(airlines, list):
            return " + ".join(airlines)
        return str(airlines)
