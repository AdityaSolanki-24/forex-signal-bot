"""
Coco OS — Social Sentiment Engine (Fixed - No SSL hangs)
=========================================================
Fixed:
1. Finnhub sentiment call removed from per-pair technical cycle
   (it was hanging on SSL and crashing Coco)
2. StockTwits forex symbols correctly mapped
3. Reddit works when credentials are set
4. All external calls wrapped with proper timeout + exception handling
"""

import requests
from config import (
    SOCIAL_SOURCE_WEIGHTS,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
)

_reddit_client = None
_reddit_warned = False


def _get_reddit_client():
    """Lazily creates Reddit client. Returns None if unavailable."""
    global _reddit_client, _reddit_warned

    if _reddit_client is not None:
        return _reddit_client

    if not REDDIT_CLIENT_ID or "YOUR_" in REDDIT_CLIENT_ID:
        if not _reddit_warned:
            _reddit_warned = True
        return None

    try:
        import praw
        _reddit_client = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        return _reddit_client
    except Exception:
        return None


# StockTwits symbol mapping
STOCKTWITS_MAP = {
    "EURUSD": None,
    "GBPUSD": None,
    "USDJPY": None,
    "AUDUSD": None,
    "USDCAD": None,
    "USDCHF": None,
    "NZDUSD": None,
    "BTC":    "BTC.X",
    "ETH":    "ETH.X",
    "XAUUSD": "GLD",
}


def get_stocktwits_sentiment(symbol):
    """Returns bullish/bearish ratio from StockTwits."""
    mapped = STOCKTWITS_MAP.get(symbol)
    if mapped is None:
        return {"bull_pct": 0.5, "bear_pct": 0.5}

    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{mapped}.json"
        response = requests.get(url, timeout=8)
        data = response.json()
        messages = data.get("messages", [])

        bull = sum(
            1 for m in messages
            if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish"
        )
        bear = sum(
            1 for m in messages
            if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish"
        )
        total = bull + bear
        if total == 0:
            return {"bull_pct": 0.5, "bear_pct": 0.5}

        return {"bull_pct": bull / total, "bear_pct": bear / total}

    except Exception:
        return {"bull_pct": 0.5, "bear_pct": 0.5}


def get_reddit_sentiment(keyword):
    """Returns bullish/bearish ratio from Reddit forex discussions."""
    client = _get_reddit_client()
    if client is None:
        return {"bull_pct": 0.5, "bear_pct": 0.5}

    try:
        from textblob import TextBlob
        subreddit = client.subreddit("forex+wallstreetbets+investing")
        bull, bear = 0, 0

        for post in subreddit.hot(limit=30):
            if keyword.lower() not in post.title.lower():
                continue
            polarity = TextBlob(post.title).sentiment.polarity
            if polarity > 0.1:
                bull += 1
            elif polarity < -0.1:
                bear += 1

        total = bull + bear
        if total == 0:
            return {"bull_pct": 0.5, "bear_pct": 0.5}

        return {"bull_pct": bull / total, "bear_pct": bear / total}

    except Exception:
        return {"bull_pct": 0.5, "bear_pct": 0.5}


def social_signal(social_symbol, reddit_keyword):
    """
    Combines StockTwits + Reddit into one social vote.
    Finnhub sentiment removed from here — it was causing
    SSL hangs on every technical cycle tick. Finnhub news
    is still active in vip_monitor.py which runs separately.

    Returns:
        {"direction": "BUY"/"SELL"/"NEUTRAL",
         "strength": 0-10,
         "reasons": [...]}
    """
    reasons = []
    score = 0.0

    # StockTwits (crypto/gold only — forex not supported)
    st = get_stocktwits_sentiment(social_symbol)
    st_w = SOCIAL_SOURCE_WEIGHTS.get("stocktwits", 0.50)
    if st["bull_pct"] >= 0.62:
        score += 5 * st_w * 2
        reasons.append(
            f"StockTwits: {int(st['bull_pct']*100)}% bullish on {social_symbol}"
        )
    elif st["bear_pct"] >= 0.62:
        score -= 5 * st_w * 2
        reasons.append(
            f"StockTwits: {int(st['bear_pct']*100)}% bearish on {social_symbol}"
        )

    # Reddit (when configured)
    rd = get_reddit_sentiment(reddit_keyword)
    rd_w = SOCIAL_SOURCE_WEIGHTS.get("reddit", 0.50)
    if rd["bull_pct"] >= 0.62:
        score += 5 * rd_w * 2
        reasons.append(
            f"Reddit: {int(rd['bull_pct']*100)}% bullish on {reddit_keyword}"
        )
    elif rd["bear_pct"] >= 0.62:
        score -= 5 * rd_w * 2
        reasons.append(
            f"Reddit: {int(rd['bear_pct']*100)}% bearish on {reddit_keyword}"
        )

    if score >= 2:
        direction = "BUY"
    elif score <= -2:
        direction = "SELL"
    else:
        direction = "NEUTRAL"

    return {
        "direction": direction,
        "strength": min(10, abs(int(score))),
        "reasons": reasons,
    }
