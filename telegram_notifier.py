# telegram_notifier.py - минималистичная версия
import requests
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

    def _send_message(self, message):
        if not self.enabled:
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except:
            pass

    def send_bot_status(self, status):
        """Сообщение о старте/стопе бота"""
        self._send_message(status)

    def send_trade_signal(self, side, price):
        """Сообщение о сигнале входа"""
        self._send_message(f"{side.upper()} @ {price:.2f}")

# глобальный инстанс
telegram = TelegramNotifier()
