"""
Coco OS — Whale Tracker  (Layer A)
======================================
Monitors large on-chain crypto transactions using Whale
Alert's API. Large exchange inflows often precede selling
pressure; large outflows often precede accumulation/holding.

If no Whale Alert key is configured, this engine simply
returns no events rather than crashing — Coco runs fine
without it, just without crypto whale signals.
"""

import time
import requests

from config import WHALE_ALERT_API_KEY, WHALE_MIN_USD_VALUE, WHALE_TRACKED_SYMBOLS

WHALE_ALERT_URL = "https://api.whale-alert.io/v1/transactions"

_last_checked_timestamp = None


def check_whale_transactions():
    """
    Returns a list of significant whale transaction events
    since the last check:

        {
            "symbol": "BTC",
            "amount_usd": 45000000,
            "from_type": "exchange",
            "to_type": "unknown",
            "direction_hint": "SELL",   # exchange outflow heuristic
        }
    """
    global _last_checked_timestamp

    if "YOUR_" in WHALE_ALERT_API_KEY:
        return []  # not configured — degrade gracefully

    now = int(time.time())
    start = _last_checked_timestamp or (now - 300)  # first run: look back 5 min

    params = {
        "api_key": WHALE_ALERT_API_KEY,
        "min_value": WHALE_MIN_USD_VALUE,
        "start": start,
        "end": now,
    }

    try:
        response = requests.get(WHALE_ALERT_URL, params=params, timeout=10)
        data = response.json()
        _last_checked_timestamp = now

        events = []
        for tx in data.get("transactions", []):
            symbol = tx.get("symbol", "").upper()
            if symbol not in WHALE_TRACKED_SYMBOLS:
                continue

            from_type = tx.get("from", {}).get("owner_type", "unknown")
            to_type = tx.get("to", {}).get("owner_type", "unknown")

            # Simple heuristic: moving FROM an exchange often
            # means accumulation/withdrawal (bullish-ish);
            # moving TO an exchange often precedes selling.
            if to_type == "exchange":
                direction_hint = "SELL"
            elif from_type == "exchange":
                direction_hint = "BUY"
            else:
                direction_hint = "NEUTRAL"

            events.append({
                "symbol": symbol,
                "amount_usd": tx.get("amount_usd", 0),
                "from_type": from_type,
                "to_type": to_type,
                "direction_hint": direction_hint,
            })

        return events

    except requests.RequestException as e:
        print(f"  ! Whale Alert fetch error: {e}")
        return []
    except ValueError as e:
        print(f"  ! Whale Alert parse error: {e}")
        return []
