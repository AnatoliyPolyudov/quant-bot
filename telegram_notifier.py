# telegram_notifier.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # ЗАГРУЖАЕМ ПЕРЕМЕННЫЕ ИЗ .env

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        print(f"[Telegram] Enabled: {self.enabled}")
        if self.enabled:
            print(f"[Telegram] Token: {TELEGRAM_BOT_TOKEN[:10]}...")
            print(f"[Telegram] Chat ID: {TELEGRAM_CHAT_ID}")

    def _send_message(self, message):
        if not self.enabled:
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            response = requests.post(url, json=payload, timeout=5)
            print(f"[Telegram] Sent: {message}")
        except Exception as e:
            print(f"[Telegram] Error: {e}")

    def send_bot_status(self, status):
        self._send_message(status)

    def send_trade_signal(self, side, price):
        self._send_message(f"{side.lower()} {price:.2f}")

telegram = TelegramNotifier()
