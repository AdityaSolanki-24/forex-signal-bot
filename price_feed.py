"""
Coco OS — Live Price Feed  (Layer A — base layer)
======================================================
Pulls live prices for every symbol in config.py using the
Twelve Data free API. Every other engine in Coco checks its
signals against this — it's the ground truth of "where is
price right now."

Each request is wrapped in error handling — if one symbol
fails (rate limit, bad symbol, connection issue), Coco logs
it and keeps going instead of crashing.
"""

import requests

from config import TWELVE_DATA_API_KEY, ALL_SYMBOLS

# A simple in-memory cache so that if Twelve Data is briefly
# unreachable, the rest of the system still has a recent
# price to work with instead of nothing at all.
_last_known_prices = {}


def get_live_price(symbol):
    """
    Fetch the current price for one symbol.
    Returns a float, or the last known cached price if the
    request fails, or None if there's no cached value either.
    """
    url = "https://api.twelvedata.com/price"
    params = {"symbol": symbol, "apikey": TWELVE_DATA_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "price" in data:
            price = float(data["price"])
            _last_known_prices[symbol] = price
            return price

        print(f"  ! Could not get price for {symbol}: {data}")
        return _last_known_prices.get(symbol)

    except requests.RequestException as e:
        print(f"  ! Connection error for {symbol}: {e}")
        return _last_known_prices.get(symbol)


def get_all_prices():
    """
    Fetch live prices for every symbol in ALL_SYMBOLS.
    Returns a dict like {"EUR/USD": 1.0832, "BTC/USD": 67250.0, ...}
    Symbols that fail (and have no cache) are left out.
    """
    prices = {}
    for symbol in ALL_SYMBOLS:
        price = get_live_price(symbol)
        if price is not None:
            prices[symbol] = price
    return prices


def pip_size(pair):
    """
    How big is 1 pip for this pair, in raw price units.
    JPY pairs use 0.01, everything else uses 0.0001.
    Crypto/commodities don't really use "pips" the same way,
    so we use a sensible price-unit equivalent.
    """
    if "JPY" in pair:
        return 0.01
    if pair in ("BTC/USD", "ETH/USD"):
        return 1.0       # 1 "pip" ≈ $1 move, just for rough scaling
    if pair in ("XAU/USD",):
        return 0.1        # gold moves in tighter increments
    return 0.0001


def price_to_pips(price_diff, pair):
    """Convert a raw price difference into a pip count."""
    size = pip_size(pair)
    return round(price_diff / size, 1)
