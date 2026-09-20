"""
Coco OS — Risk Environment Engine  (Layer C, engine 4 of 4)
==================================================================
Reads VIX (the market "fear gauge") and applies a risk-on /
risk-off bias adjustment to every signal. Also houses the
multi-timeframe confluence check (verification step 5) and
the black-swan circuit breaker (verification step 7-adjacent).

VIX above config.VIX_RISK_OFF_LEVEL -> safe-haven currencies
(USD, CHF, JPY, Gold) get a confidence boost on bullish signals.

VIX below config.VIX_RISK_ON_LEVEL -> risk-on currencies
(AUD, NZD) get a confidence boost on bullish signals.
"""

import requests

from config import (
    VIX_RISK_OFF_LEVEL, VIX_RISK_ON_LEVEL, VIX_BLACK_SWAN_JUMP,
    MTF_CONFLICT_PENALTY,
)

SAFE_HAVEN_PAIRS = {"USD/CHF", "USD/JPY", "XAU/USD"}
RISK_ON_PAIRS = {"AUD/USD", "NZD/USD"}

_vix_history = []  # keeps last few readings for the black-swan jump check


def get_vix():
    """
    Fetches the current VIX level using Yahoo Finance's public
    chart endpoint (no key needed). Returns a float, or the
    last known value if the request fails.
    """
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        vix = float(price)

        _vix_history.append(vix)
        if len(_vix_history) > 12:  # keep roughly the last hour at 5-min checks
            _vix_history.pop(0)

        return vix

    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"  ! VIX fetch error: {e}")
        return _vix_history[-1] if _vix_history else 16.0  # calm-market default


def check_black_swan():
    """
    Returns True if VIX has jumped more than
    config.VIX_BLACK_SWAN_JUMP within the recent history window.
    """
    if len(_vix_history) < 2:
        return False
    jump = max(_vix_history) - min(_vix_history)
    return jump >= VIX_BLACK_SWAN_JUMP


def risk_environment_adjustment(pair, vix):
    """
    Returns a confidence ADJUSTMENT (can be positive or
    negative) and a reason string, or (0, None) if VIX is in
    the normal range for this pair.
    """
    if vix >= VIX_RISK_OFF_LEVEL and pair in SAFE_HAVEN_PAIRS:
        return 10, f"VIX elevated ({vix:.1f}) — risk-off favors safe havens"

    if vix <= VIX_RISK_ON_LEVEL and pair in RISK_ON_PAIRS:
        return 10, f"VIX low ({vix:.1f}) — risk-on favors {pair}"

    if vix >= VIX_RISK_OFF_LEVEL and pair in RISK_ON_PAIRS:
        return -10, f"VIX elevated ({vix:.1f}) — risk-off pressures {pair}"

    return 0, None


def check_mtf_confluence(direction_htf, direction_ltf):
    """
    Multi-timeframe confluence check (verification step 5).
    direction_htf = higher timeframe direction ("BUY"/"SELL"/"NEUTRAL")
    direction_ltf = lower timeframe direction

    Returns (confluence_ok: bool, penalty_multiplier: float)
    """
    if direction_htf == "NEUTRAL" or direction_ltf == "NEUTRAL":
        return True, 1.0  # not enough info to call it a conflict

    if direction_htf == direction_ltf:
        return True, 1.0

    return False, (1.0 - MTF_CONFLICT_PENALTY)
