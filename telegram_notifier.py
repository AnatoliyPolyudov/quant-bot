# telegram_notifier.py - минималистичная версия
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        if self.enabled:
            print("✅ Telegram notifications ENABLED")
        else:
            print("❌ Telegram notifications DISABLED - check tokens")

    def _send_message(self, message: str):
        if not self.enabled:
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"❌ Telegram send error: {e}")

    def send_bot_status(self, status: str):
        """Сообщение о старте/стопе бота"""
        self._send_message(status.upper())

    def send_trade_signal(self, action, side, price, size=0, reason="", metrics=None):
        """Минималистичное уведомление о сигнале входа"""
        self._send_message(f"{side.upper()} @ {price:.2f}")

# глобальный инстанс
telegram = TelegramNotifier()
