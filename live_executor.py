# live_executor.py
"""
Live executor for OKX (USDT-Margined Perpetuals).
SAFE BY DEFAULT: DRY_RUN = True.
Use with care. Test in sandbox first.
Requires 'requests'.
"""
import os
import time
import json
import hmac
import base64
import hashlib
import requests
import csv
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from config import SYMBOL, LOGS_DIR, START_EQUITY, POSITION_PCT

# Env vars: set OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE for live mode
API_KEY = os.getenv("OKX_API_KEY", "")
API_SECRET = os.getenv("OKX_API_SECRET", "")
API_PASSPHRASE = os.getenv("OKX_API_PASSPHRASE", "")

# Safety defaults
DRY_RUN = True
MIN_NOTIONAL_USDT = 5.0
OKX_API_BASE = "https://www.okx.com"
OKX_MARKET_TICKER = "/api/v5/market/ticker"
OKX_TRADE_ORDER = "/api/v5/trade/order"
OKX_ACCOUNT_POSITIONS = "/api/v5/account/positions"

LOGFILE = LOGS_DIR / "live_trades.csv"
if not LOGFILE.exists():
    with open(LOGFILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ts","mode","action","side","price","size_contracts","notional_usdt","note","api_response"])

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def _sign(timestamp: str, method: str, request_path: str, body: str, secret: str):
    message = timestamp + method.upper() + request_path + (body or "")
    mac = hmac.new(bytes(secret, "utf-8"), bytes(message, "utf-8"), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def _request(method: str, path: str, params=None, body: dict=None, timeout=10.0):
    url = OKX_API_BASE + path
    method = method.upper()
    ts = datetime.utcnow().isoformat() + "Z"
    body_str = json.dumps(body) if body else ""
    if API_KEY and API_SECRET and API_PASSPHRASE:
        sign = _sign(ts, method, path, body_str, API_SECRET)
        headers = {
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
            "Content-Type": "application/json"
        }
    else:
        headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
        else:
            r = requests.post(url, params=params, data=body_str, headers=headers, timeout=timeout)
        return r
    except Exception as e:
        return None

def log_row(mode, action, side, price, size_contracts, notional_usdt, note, api_response):
    ts = datetime.utcnow().isoformat()
    with open(LOGFILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ts, mode, action, side, price, size_contracts, notional_usdt, note, json.dumps(api_response)])
    print(f"[{ts}] {mode} {action} {side} price={price} size={size_contracts} notional={notional_usdt} note={note}")

class LiveExecutor:
    def __init__(self, dry_run=True):
        # If API keys are not set, force dry_run
        self.dry_run = dry_run or (API_KEY == "" or API_SECRET == "" or API_PASSPHRASE == "")
        if self.dry_run:
            print("LIVE EXECUTOR: DRY_RUN mode (no real orders).")
        else:
            print("LIVE EXECUTOR: LIVE mode (orders WILL be sent).")
        self.session = requests.Session()

    def get_price(self, instId):
        params = {"instId": instId}
        r = _request("GET", OKX_MARKET_TICKER, params=params)
        if not r or r.status_code != 200:
            return None
        try:
            data = r.json()
            if data.get("code") == "0" and data.get("data"):
                rec = data["data"][0]
                return float(rec.get("last"))
            return None
        except Exception:
            return None

    def _place_market_order(self, instId, side, sz_contracts, tdMode="cross", reduceOnly=False):
        body = {
            "instId": instId,
            "side": side,
            "ordType": "market",
            "sz": str(sz_contracts),
            "tdMode": tdMode
        }
        if reduceOnly:
            body["reduceOnly"] = True

        if self.dry_run:
            resp = {"sim": True, "body": body}
            log_row("DRY", "ORDER", side, None, sz_contracts, None, "simulated_market_order", resp)
            return resp

        r = _request("POST", OKX_TRADE_ORDER, body=body)
        if r is None:
            log_row("ERR", "ORDER", side, None, sz_contracts, None, "http_error", {})
            return None
        try:
            resp = r.json()
        except Exception:
            resp = {"status_code": r.status_code, "text": r.text}
        log_row("LIVE", "ORDER", side, None, sz_contracts, None, "okx_resp", resp)
        return resp

    def enter_position_notional(self, side, notional_usdt):
        notional_usdt = float(notional_usdt)
        if notional_usdt < MIN_NOTIONAL_USDT:
            print("Notional below minimum:", notional_usdt)
            return None

        price = self.get_price(SYMBOL)
        if not price:
            print("Failed to fetch price; abort enter")
            return None

        size = Decimal(notional_usdt / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        if size <= 0:
            print("Calculated size zero; abort")
            return None

        resp = self._place_market_order(SYMBOL, "buy" if side.upper()=="LONG" else "sell", str(size))
        return {"price": price, "size": float(size), "resp": resp, "notional": notional_usdt}

    def exit_position_market(self):
        if self.dry_run:
            resp = {"sim": True, "note": "simulated_exit"}
            log_row("DRY", "EXIT", "BOTH", None, None, None, "simulated_exit", resp)
            return resp

        # live exit: query positions (user must adapt if OKX returns unexpected structure)
        params = {"instId": SYMBOL}
        r = _request("GET", OKX_ACCOUNT_POSITIONS, params=params)
        if not r or r.status_code != 200:
            print("Failed to query positions")
            return None
        try:
            data = r.json()
        except Exception:
            data = None
        log_row("LIVE", "EXIT", "BOTH", None, None, None, "position_query", data)
        return data

    def safe_enter_from_equity_pct(self, side, pct):
        equity = START_EQUITY
        notional = equity * pct
        return self.enter_position_notional(side, notional)
