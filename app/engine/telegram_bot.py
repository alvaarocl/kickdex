"""
Telegram Bot Engine — Notificaciones proactivas de KICKDEX.
Envía alertas de valor y resúmenes de mercado directamente al móvil.
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class KICKDEXTelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str) -> bool:
        """Envía un mensaje de texto plano."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram Bot no configurado (Token o ChatID ausentes).")
            return False
        
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            res = requests.post(f"{self.base_url}/sendMessage", json=payload)
            res.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False

    def alert_value_bet(self, match: str, market: str, odds: float, ev: float):
        """Envía una alerta formateada de Value Bet."""
        emoji = "🟢" if ev > 0.10 else "🟡"
        msg = (
            f"<b>{emoji} KICKDEX VALUE ALERT</b>\n\n"
            f"⚽ Partido: <b>{match}</b>\n"
            f"🎯 Mercado: {market}\n"
            f"💰 Cuota: <b>{odds:.2f}</b>\n"
            f"📈 EV Detectado: <b>{ev*100:+.1f}%</b>\n\n"
            f"<i>Analiza el partido en kickdex.com</i>"
        )
        return self.send_message(msg)

if __name__ == "__main__":
    # Test simple
    bot = KICKDEXTelegramBot()
    bot.send_message("🤖 KICKDEX Engine Online — Terminal Pro")
