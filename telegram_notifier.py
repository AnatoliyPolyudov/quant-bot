# telegram_notifier.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import requests
import json
import os
from datetime import datetime

# Настройки Telegram из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8468371553:AAE5XfnFkgkeadWt2M44w8BsiTQ8-7dogFU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "317217451")

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        
        if self.enabled:
            print("✅ Telegram notifications ENABLED")
        else:
            print("❌ Telegram notifications DISABLED - check tokens")

    def _send_message(self, message, parse_mode="HTML"):
        """Базовая отправка сообщения"""
        if not self.enabled:
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def send_trade_signal(self, action, side, price, size, reason, metrics):
        """Уведомление о торговом сигнале"""
        if not self.enabled:
            return
            
        time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        
        message = f"""
🎯 <b>TRADE SIGNAL</b>
⏰ {time_str}
⚡ <b>{action} {side}</b>

💰 Price: ${price:,.2f}
📊 Size: {size:.6f} BTC
📈 Reason: {reason}

<b>METRICS:</b>
📊 Imbalance: {metrics.get('imbalance', 0):.3f}
📈 Delta: {metrics.get('delta', 0):.1f}
🎯 Trend: {metrics.get('trend', 'N/A')}
🔁 Delta/min: {metrics.get('delta_per_minute', 0):.1f}
        """.strip()

        self._send_message(message)

    def send_trade_executed(self, action, side, price, size, notional, order_id=None):
        """Уведомление о исполненной сделке"""
        if not self.enabled:
            return
            
        time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        status = "🟢 LIVE" if order_id and "sim" not in str(order_id) else "🟡 DRY RUN"
        
        message = f"""
✅ <b>TRADE EXECUTED</b>
⏰ {time_str}
{status}

🔄 <b>{action} {side}</b>
💰 Price: ${price:,.2f}
📊 Size: {size:.6f} BTC
💵 Notional: ${notional:.2f}

{"📝 Order: " + str(order_id) if order_id else ""}
        """.strip()

        self._send_message(message)

    def send_trade_exit(self, side, entry_price, exit_price, pnl_percent, hold_time_minutes):
        """Уведомление о выходе из позиции"""
        if not self.enabled:
            return
            
        time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        pnl_emoji = "🟢" if pnl_percent > 0 else "🔴" if pnl_percent < 0 else "⚪"
        side_emoji = "📈" if side == "LONG" else "📉"
        
        message = f"""
📤 <b>POSITION CLOSED</b>
⏰ {time_str}
🕒 Hold: {hold_time_minutes:.1f}m

{side_emoji} {side}
💰 Entry: ${entry_price:,.2f}
💰 Exit: ${exit_price:,.2f}

{pnl_emoji} PnL: {pnl_percent:+.3f}%
        """.strip()

        self._send_message(message)

    def send_error(self, error_message):
        """Уведомление об ошибке"""
        if not self.enabled:
            return
            
        time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        
        message = f"""
🚨 <b>BOT ERROR</b>
⏰ {time_str}

❌ {error_message}
        """.strip()

        self._send_message(message)

    def send_bot_status(self, status, version="1.0"):
        """Уведомление о статусе бота"""
        if not self.enabled:
            return
            
        time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        
        message = f"""
🤖 <b>QUANT BOT {version}</b>
⏰ {time_str}

📊 Status: <b>{status}</b>
📍 Symbol: BTC-USDT-SWAP
⏱️ Timeframe: 1-MINUTE
🔧 Mode: LIVE TRADING
        """.strip()

        self._send_message(message)


# Глобальный инстанс
telegram = TelegramNotifier()
