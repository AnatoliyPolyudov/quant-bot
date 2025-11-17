# telegram_notifier.py
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        print(f"[Telegram] Enabled: {self.enabled}")

    def _send_message(self, message):
        if not self.enabled:
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(url, json=payload, timeout=5)
        except:
            pass

    def send_bot_status(self, status):
        self._send_message(status)

    def send_trade_signal(self, side, price):
        self._send_message(f"{side.lower()} {price:.2f}")

telegram = TelegramNotifier()