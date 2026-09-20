"""

import os
from dotenv import load_dotenv

load_dotenv()

Coco OS — Master Configuration
=================================
Every setting Coco needs lives here. Fill in your free API
keys, then leave this file alone — every other file reads
from it.

NEVER share this file or upload it publicly — it holds your
private keys.
"""

# ══════════════════════════════════════════════════════════
# API KEYS — fill these in (see README.md for where to get each)
# ══════════════════════════════════════════════════════════

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CocoOS/1.0")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Optional — Whale Alert free tier (whale_alert.py works without
# this too, using a public fallback, but a real key is sturdier)
WHALE_ALERT_API_KEY = os.getenv("WHALE_ALERT_API_KEY", "")


# ══════════════════════════════════════════════════════════
# SYMBOLS COCO MONITORS
# ══════════════════════════════════════════════════════════

FOREX_SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"]
CRYPTO_SYMBOLS = ["BTC/USD"]
COMMODITY_SYMBOLS = ["XAU/USD"]

ALL_SYMBOLS = FOREX_SYMBOLS + CRYPTO_SYMBOLS + COMMODITY_SYMBOLS

# Used by the social/sentiment engine — StockTwits & Reddit
# use plain tickers without the slash
SOCIAL_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "BTC", "XAUUSD"]


# ══════════════════════════════════════════════════════════
# TIMING
# ══════════════════════════════════════════════════════════

MAIN_LOOP_INTERVAL_SECONDS = 30          # Coco's heartbeat — every layer ticks off this

PRICE_CHECK_EVERY_N_TICKS = 3            # → every 5 min
CALENDAR_CHECK_EVERY_N_TICKS = 10        # → every 60 min
COT_CHECK_EVERY_N_TICKS = 1440           # → roughly once a day (real trigger is day-of-week)
SOCIAL_CHECK_EVERY_N_TICKS = 2           # → every ~2 min
VIP_CHECK_EVERY_N_TICKS = 2              # → every tick (this list is tiny, cost is near-zero)
WHALE_CHECK_EVERY_N_TICKS = 1            # → every tick
VIX_CHECK_EVERY_N_TICKS = 5              # → every 5 min
REWEIGHT_EVERY_N_SIGNALS = 200           # self-improvement cycle

PRE_EVENT_ALERT_MINUTES_BEFORE = 30
REVERSAL_CHECK_MINUTES_AFTER = 5


# ══════════════════════════════════════════════════════════
# CONFIDENCE & RISK THRESHOLDS
# ══════════════════════════════════════════════════════════

CONFIDENCE_THRESHOLD = 45          # signals below this are never sent
HIGH_CONFIDENCE_THRESHOLD = 85     # flagged as "high confidence" in the message

VIX_RISK_OFF_LEVEL = 25            # above this → safe-haven bias applied
VIX_RISK_ON_LEVEL = 15             # below this → risk-on bias applied
VIX_BLACK_SWAN_JUMP = 15           # VIX +this much in 1hr → suspend all signals

RETAIL_SENTIMENT_EXTREME = 0.65    # 65%+ one-sided → contrarian signal triggers

NEWS_BLACKOUT_MINUTES = 30         # no technical signals ± this many min around news
SPREAD_ABNORMAL_MULTIPLIER = 3.0   # spread > 3x normal average → block signal

MTF_CONFLICT_PENALTY = 0.40        # confidence multiplier when timeframes disagree
ANOMALY_STD_DEV_THRESHOLD = 3.0    # data point flagged if this many std devs from norm


# ══════════════════════════════════════════════════════════
# SOURCE WEIGHTS — how much each engine's vote counts
# (must sum to 1.0 — used by the confluence engine)
# ══════════════════════════════════════════════════════════

SOURCE_WEIGHTS = {
    "institutional": 0.30,   # COT + retail sentiment contrarian signal
    "news": 0.30,             # economic calendar deviation
    "social": 0.20,           # StockTwits + Reddit + VIP posts
    "technical": 0.20,        # SMC + VIX + risk environment
}

# Social engine internal split (must sum to 1.0)
SOCIAL_SOURCE_WEIGHTS = {
    "stocktwits": 0.40,
    "reddit": 0.35,
    "vip_post": 0.25,
}


# ══════════════════════════════════════════════════════════
# VIP WATCHLIST — accounts/sources that bypass the normal
# cycle and trigger the emergency pipeline
# ══════════════════════════════════════════════════════════
# NOTE: official accounts change over time (e.g. a new Fed
# Chair). Update this list whenever a role changes hands —
# Coco's news scanner will flag this in its daily report if
# it detects a "new [role] sworn in" headline.

VIP_WATCHLIST = [
    # US Government — highest impact
    {"name": "Trump", "platform": "truthsocial", "handle": "realDonaldTrump", "weight": 1.0},
    {"name": "Federal Reserve", "platform": "x", "handle": "federalreserve", "weight": 0.9},
    {"name": "Fed Chair Warsh", "platform": "x", "handle": "KevinWarsh", "weight": 0.95},
    {"name": "US Treasury", "platform": "x", "handle": "USTreasury", "weight": 0.85},
    {"name": "White House", "platform": "x", "handle": "WhiteHouse", "weight": 0.8},

    # Europe
    {"name": "ECB", "platform": "x", "handle": "ecb", "weight": 0.85},
    {"name": "Lagarde", "platform": "x", "handle": "Lagarde", "weight": 0.85},

    # UK
    {"name": "Bank of England", "platform": "x", "handle": "bankofengland", "weight": 0.8},

    # Japan
    {"name": "Bank of Japan", "platform": "x", "handle": "Bank_of_Japan_e", "weight": 0.8},

    # Oil
    {"name": "OPEC", "platform": "x", "handle": "OPECSecretariat", "weight": 0.75},

    # Crypto
    {"name": "Elon Musk", "platform": "x", "handle": "elonmusk", "weight": 0.85},
    {"name": "Michael Saylor", "platform": "x", "handle": "saylor", "weight": 0.75},
    {"name": "SEC", "platform": "x", "handle": "SECGov", "weight": 0.8},

    # ── YOUR 3 NEW ACCOUNTS ──────────────────────────
    {"name": "Unusual Whales", "platform": "x", "handle": "unusual_whales", "weight": 0.85},
    {"name": "Financial Juice", "platform": "x", "handle": "financialjuice", "weight": 0.90},
    {"name": "Walter Bloomberg", "platform": "x", "handle": "DeItaone", "weight": 0.92},
]

VIP_KEYWORDS = [
    # Emoji triggers — these accounts use emojis for impact
    "🚨", "‼️", "🔴", "🟢", "⚡", "🐋", "BREAKING",
    "JUST IN", "FLASH", "ALERT", "NOW:",

    # Financial Juice / Walter Bloomberg specific
    "bps", "basis points", "cut rates", "hike rates",
    "beats", "misses", "in line", "surprise",
    "above expectations", "below expectations",
    "revised", "prior", "previous",

    # Unusual Whales specific
    "unusual options", "dark pool", "congress",
    "insider", "flow", "calls", "puts",

    # Standard keywords already there
    "tariff", "tariffs", "trade deal", "trade war",
    "sanction", "sanctions", "embargo",
    "rate hike", "rate cut", "interest rate",
    "hawkish", "dovish", "inflation", "stimulus",
    "recession", "gdp", "unemployment", "jobs", "payroll",
    "default", "debt ceiling", "shutdown",
    "war", "attack", "ceasefire", "emergency",
    "bitcoin", "btc", "ethereum", "crypto",
    "oil", "opec", "crude",
    "dollar", "usd", "euro", "yen", "pound",
    "ISM", "PMI", "manufacturing", "ADP", "employment change",
    "Warsh", "Bailey", "Lagarde", "rate hike", "hawkish",
    "jobs", "payrolls", "labor market", "nonfarm",
    "manufacturing pmi", "factory", "production",
]


# ══════════════════════════════════════════════════════════
# ECONOMIC EVENTS COCO TRACKS
# ══════════════════════════════════════════════════════════
# match              -> substring to match against the calendar title
# currency           -> country code the event belongs to
# typical_deviation  -> a "normal sized surprise" for this event
#                       (same units as forecast/actual)
# base_pips          -> (low, high) typical pip range for a
#                       normal-sized surprise on affected pairs
# pairs              -> {pair: "direct"/"inverse"}
#                       "direct"  = stronger currency pushes pair UP
#                       "inverse" = stronger currency pushes pair DOWN

NEWS_EVENTS = {
    "NFP": {
        "match": "Non-Farm",
        "currency": "USD",
        "typical_deviation": 30,
        "base_pips": (50, 120),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "GBP/USD": "inverse",
            "XAU/USD": "inverse",
        },
    },
    "CPI": {
        "match": "CPI",
        "currency": "USD",
        "typical_deviation": 0.1,
        "base_pips": (40, 90),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "GBP/USD": "inverse",
        },
    },
    "Core CPI": {
        "match": "Core CPI",
        "currency": "USD",
        "typical_deviation": 0.1,
        "base_pips": (40, 95),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "Core PPI": {
        "match": "Core PPI",
        "currency": "USD",
        "typical_deviation": 0.1,
        "base_pips": (30, 70),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "GDP": {
        "match": "GDP",
        "currency": "USD",
        "typical_deviation": 0.2,
        "base_pips": (30, 65),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "ISM Manufacturing": {
        "match": "ISM Manufacturing",
        "currency": "USD",
        "typical_deviation": 1.0,
        "base_pips": (25, 55),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "ADP Employment": {
        "match": "ADP",
        "currency": "USD",
        "typical_deviation": 30,
        "base_pips": (25, 65),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "GBP/USD": "inverse",
            "XAU/USD": "inverse",
        },
    },
    "Retail Sales": {
        "match": "Retail Sales",
        "currency": "USD",
        "typical_deviation": 0.3,
        "base_pips": (25, 55),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "FOMC": {
        "match": "FOMC",
        "currency": "USD",
        "typical_deviation": 0.25,
        "base_pips": (60, 150),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "XAU/USD": "inverse",
        },
    },
    "Unemployment Claims": {
        "match": "Unemployment Claims",
        "currency": "USD",
        "typical_deviation": 10,
        "base_pips": (20, 45),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    },
    "ECB Rate": {
        "match": "ECB",
        "currency": "EUR",
        "typical_deviation": 0.25,
        "base_pips": (50, 120),
        "pairs": {
            "EUR/USD": "direct",
            "EUR/JPY": "direct",
        },
    },
    "BOE Rate": {
        "match": "BOE",
        "currency": "GBP",
        "typical_deviation": 0.25,
        "base_pips": (50, 110),
        "pairs": {
            "GBP/USD": "direct",
        },
    },
    "ISM Manufacturing": {
        "match": "ISM Manufacturing",
        "currency": "USD",
        "typical_deviation": 1.0,
        "base_pips": (25, 60),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "XAU/USD": "inverse",
        },
    },
    "BOJ Rate": {
        "match": "BOJ",
        "currency": "JPY",
        "typical_deviation": 0.1,
        "base_pips": (60, 140),
        "pairs": {
            "USD/JPY": "inverse",
        },
    },
    "ADP": {
        "match": "ADP",
        "currency": "USD",
        "typical_deviation": 30,
        "base_pips": (25, 60),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
        },
    "Fed Speaks": {
        "match": "Fed Chair",
        "currency": "USD",
        "typical_deviation": 0.0,
        "base_pips": (30, 80),
        "pairs": {
            "EUR/USD": "inverse",
            "USD/JPY": "direct",
            "XAU/USD": "inverse",
        },
    },
    "BOE Speaks": {
        "match": "BOE Gov",
        "currency": "GBP",
        "typical_deviation": 0.0,
        "base_pips": (30, 70),
        "pairs": {
            "GBP/USD": "direct",
            "EUR/GBP": "direct",
        },
    },
    },
}


# ══════════════════════════════════════════════════════════
# WHALE TRACKER SETTINGS
# ══════════════════════════════════════════════════════════

WHALE_MIN_USD_VALUE = 1_000_000   # only alert on transfers at/above this size
WHALE_TRACKED_SYMBOLS = ["BTC", "ETH"]


# ══════════════════════════════════════════════════════════
# DATABASE / LOGGING
# ══════════════════════════════════════════════════════════

DATABASE_PATH = "coco_signals.db"
LOG_FILE_PATH = "coco_log.txt"

# Outcomes are checked this long after a signal fires
OUTCOME_CHECK_HOURS = [1, 4, 24]
