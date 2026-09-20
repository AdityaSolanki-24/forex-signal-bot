"""
Coco OS — VIP Monitor (Final Fixed Version)
============================================
Fixes:
1. FinBERT/transformers completely removed — was hanging on import
2. Finnhub timeout reduced to 8s with proper exception handling
3. No SSL hangs — all calls have hard timeouts
4. Keyword scoring used instead of AI model — instant and reliable
"""

import requests
from bs4 import BeautifulSoup
from config import VIP_WATCHLIST, VIP_KEYWORDS, FINNHUB_API_KEY

_last_seen_post = {}
_last_finnhub_headlines = set()

import time as _time
FINNHUB_MAX_AGE_MINUTES = 45


def _score_sentiment(text):
    """
    Keyword-based sentiment scoring.
    Fast, instant, no model loading required.
    """
    text_lower = text.lower()

    bearish_words = [
        "tariff", "tariffs", "sanction", "ban", "war", "attack",
        "default", "shutdown", "hawkish", "hike", "tighten",
        "recession", "crisis", "crash", "collapse", "downgrade",
        "above expectations", "beats forecast", "hot", "surge",
    ]
    bullish_words = [
        "deal", "agreement", "ceasefire", "stimulus", "dovish",
        "cut rates", "rate cut", "easing", "recovery", "growth",
        "below expectations", "misses forecast", "weak", "cool",
        "better than expected",
    ]

    bear_hits = sum(1 for w in bearish_words if w in text_lower)
    bull_hits = sum(1 for w in bullish_words if w in text_lower)

    if bear_hits > bull_hits:
        return "BEARISH", min(90, 50 + bear_hits * 10)
    elif bull_hits > bear_hits:
        return "BULLISH", min(90, 50 + bull_hits * 10)
    return "NEUTRAL", 40


def _contains_keywords(text):
    """Check if text contains any market-moving keywords."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in VIP_KEYWORDS)


def _scrape_truthsocial(handle):
    """Scrapes Truth Social with SSL workaround."""
    url = f"https://truthsocial.com/@{handle}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(
            url, headers=headers, timeout=10, verify=False
        )
        soup = BeautifulSoup(response.content, "html.parser")
        posts = soup.find_all("div", class_="status__content")
        if posts:
            return posts[0].get_text().strip()
        return None
    except Exception as e:
        print(f"  ! Truth Social error for {handle}: {e}")
        return None


def _get_finnhub_vip_news():
    """
    Gets latest financial news from Finnhub.
    Hard 8-second timeout — never hangs.
    Only processes headlines from last 45 minutes.
    """
    if not FINNHUB_API_KEY or "YOUR_" in FINNHUB_API_KEY:
        return []

    try:
        url = "https://finnhub.io/api/v1/news"
        params = {
            "category": "general",
            "token": FINNHUB_API_KEY,
        }
        # Hard 8-second timeout — will not hang
        response = requests.get(url, params=params, timeout=8)
        articles = response.json()

        now_unix = _time.time()
        cutoff_unix = now_unix - (FINNHUB_MAX_AGE_MINUTES * 60)

        fresh_count = 0
        results = []

        for article in articles[:20]:
            published_unix = article.get("datetime", 0)

            if published_unix < cutoff_unix:
                continue

            fresh_count += 1
            headline = article.get("headline", "")
            summary = article.get("summary", "")
            full_text = f"{headline} {summary}"

            if headline in _last_finnhub_headlines:
                continue

            if not _contains_keywords(full_text):
                continue

            sentiment, confidence = _score_sentiment(full_text)
            if sentiment == "NEUTRAL":
                continue

            age_minutes = round((now_unix - published_unix) / 60)

            _last_finnhub_headlines.add(headline)
            if len(_last_finnhub_headlines) > 100:
                try:
                    _last_finnhub_headlines.pop()
                except Exception:
                    pass

            results.append({
                "name": "Finnhub News",
                "text": headline[:200],
                "sentiment": sentiment,
                "confidence": confidence,
                "weight": 0.75,
                "age_minutes": age_minutes,
                "pair": detect_relevant_pair(full_text),
            })

        print(f"  > Finnhub check: {len(articles)} pulled, "
              f"{fresh_count} within {FINNHUB_MAX_AGE_MINUTES}min, "
              f"{len(results)} matched keywords")

        return results

    except requests.exceptions.Timeout:
        print("  ! Finnhub timeout — skipping this tick")
        return []
    except Exception as e:
        print(f"  ! Finnhub news error: {e}")
        return []


PAIR_KEYWORD_MAP = [
    (["gold", "xau", "bullion"], "XAU/USD"),
    (["oil", "crude", "opec", "wti", "brent"], "USD/CAD"),
    (["bitcoin", "btc", "crypto"], "BTC/USD"),
    (["ethereum", "eth"], "ETH/USD"),
    (["euro", "eur", "ecb", "lagarde", "eurozone"], "EUR/USD"),
    (["pound", "gbp", "boe", "bailey", "uk ", "britain"], "GBP/USD"),
    (["yen", "jpy", "boj", "japan"], "USD/JPY"),
    (["aussie", "aud", "rba", "australia"], "AUD/USD"),
    (["loonie", "cad", "canada", "boc"], "USD/CAD"),
    (["franc", "chf", "snb", "swiss"], "USD/CHF"),
    (["kiwi", "nzd", "rbnz", "new zealand"], "NZD/USD"),
]


def detect_relevant_pair(text):
    """Detects which forex pair a headline is about."""
    text_lower = text.lower()
    for keywords, pair in PAIR_KEYWORD_MAP:
        if any(kw in text_lower for kw in keywords):
            return pair
    usd_words = ["fed", "tariff", "treasury", "white house",
                 "powell", "warsh", "inflation", "rate hike",
                 "rate cut", "nfp", "payroll", "ism", "adp"]
    if any(w in text_lower for w in usd_words):
        return "EUR/USD"
    return "EUR/USD"


def check_vip_posts():
    """
    Main function — checks Truth Social and Finnhub.
    Returns list of market-moving event dicts.
    """
    events = []

    # Truth Social (Trump)
    for account in VIP_WATCHLIST:
        if account["platform"] != "truthsocial":
            continue

        text = _scrape_truthsocial(account["handle"])
        if not text:
            continue

        if _last_seen_post.get(account["handle"]) == text:
            continue
        _last_seen_post[account["handle"]] = text

        if not _contains_keywords(text):
            continue

        sentiment, confidence = _score_sentiment(text)
        if sentiment == "NEUTRAL":
            continue

        print(f"  > VIP post: {account['name']} — {sentiment}")
        events.append({
            "name": account["name"],
            "text": text[:200],
            "sentiment": sentiment,
            "confidence": confidence,
            "weight": account["weight"],
            "pair": detect_relevant_pair(text),
        })

    # Finnhub news
    finnhub_events = _get_finnhub_vip_news()
    if finnhub_events:
        print(f"  > Finnhub VIP: {len(finnhub_events)} signals")
    events.extend(finnhub_events)

    return events
