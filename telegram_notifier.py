# telegram_notifier.py
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        print(f"[Telegram] Enabled: {self.enabled}, Token: {bool(TELEGRAM_BOT_TOKEN)}, Chat: {bool(TELEGRAM_CHAT_ID)}")

    def _send_message(self, message):
        if not self.enabled:
            print(f"[Telegram] Skip (disabled): {message}")
            return
            
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            print(f"[Telegram] Response: {response.status_code}")
        except Exception as e:
            print(f"[Telegram] Error: {e}")

    def send_bot_status(self, status):
        msg = f"🤖 Bot <b>{status.upper()}</b>"
        self._send_message(msg)

    def send_trade_signal(self, side, price):
        msg = f"🎯 <b>{side.upper()}</b> signal\nPrice: <code>{price:.2f}</code>"
        self._send_message(msg)

telegram = TelegramNotifier()