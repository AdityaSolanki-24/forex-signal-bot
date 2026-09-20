# Coco OS — Full System

Coco is a fully automated, 24/7 forex/crypto signal system.
It watches economic news, institutional positioning (COT),
retail sentiment, social media, VIP accounts (Trump/Fed/etc),
and crypto whale moves — then sends BUY/SELL signals with a
pip target range and stop-loss straight to your Telegram.

The project is designed to support free or low-cost API tiers where available. API limits, terms, and pricing can change.

## What's in this folder

| File | Layer | What it does |
|---|---|---|
| `config.py` | — | All settings and API keys — fill this in first |
| `database.py` | L | Logs every signal, tracks accuracy over time |
| `coco_format.py` | I, K | Builds every Telegram message Coco sends |
| `telegram_bot.py` | K | Sends messages to your Telegram |
| `price_feed.py` | A | Live prices — the base layer everything checks against |
| `econ_calendar.py` | A | Economic calendar (Forex Factory, no key needed) |
| `news_engine.py` | A,C,F,I | Pre-event alerts + actual-vs-forecast signal logic |
| `cot_sentiment.py` | C | Institutional bias (COT) + retail sentiment contrarian signal |
| `social_engine.py` | C | StockTwits + Reddit sentiment |
| `vip_monitor.py` | A,G | Trump/Fed/ECB/BOJ post detection — the fast emergency path |
| `whale_alert.py` | A | Crypto whale transaction tracker |
| `risk_environment.py` | C | VIX, risk-on/risk-off bias, black swan circuit breaker |
| `coco_engine.py` | D,E,F,G,H | Combines everything, verifies, scores confidence, decides |
| `technical_signal.py` | — | Runs the continuous 5-min confluence scan |
| `main.py` | — | **Run this one** — ties every layer together on schedule |

## Setup — about 30-40 minutes total

### 1. Install Python
Download Python 3.10+ from python.org/downloads.
Check "Add Python to PATH" during install.

### 2. Install dependencies
Open a terminal in this folder and run:

    pip install -r requirements.txt

(The `torch`/`transformers` install can take a few minutes —
that's normal, it's the FinBERT NLP model.)

### 3. Get your free API keys

**Twelve Data** (live prices)
1. twelvedata.com → sign up free → copy API key

**Telegram Bot**
1. Open Telegram, search **@BotFather**
2. Send `/newbot`, choose a name + username ending in `_bot`
3. Copy the token BotFather gives you
4. Send any message to your new bot
5. Visit `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
6. Find `"chat":{"id":123456789` — that's your chat ID

**Reddit** (optional — social engine works without it,
just runs on StockTwits alone)
1. reddit.com/prefs/apps → Create App → choose "script"
2. Copy the client ID (under the app name) and secret

**Whale Alert** (optional — crypto whale signals only)
1. whale-alert.io → request a free API key

**Finnhub / FRED** (reserved for future expansion —
not required for this build to run)

### 4. Fill in config.py
Open `config.py` and paste your keys into the top section.
Leave any key as `"YOUR_..._HERE"` and Coco will simply skip
that feature gracefully — nothing crashes.

### 5. Run Coco

    python main.py

## What you'll see

- A startup message on Telegram confirming every layer is live
- VIP and whale checks every ~60 seconds
- News pre-alerts 30 minutes before high-impact releases
- Main news signals within seconds of an actual release
- Technical confluence signals roughly every 5-10 minutes,
  only when confidence clears 55%
- A terminal log showing what Coco is checking in real time

## Important honesty note

The "AI confluence engine" runs on weighted-rules scoring
from day one (see `coco_engine.py`) — this is intentional.
There's no signal history to train a machine learning model
on yet. Once `database.py` has logged 200+ signals, that's
the natural point to swap in a trained XGBoost/LSTM model in
`combine_signals()` — the function's inputs and outputs stay
exactly the same, so nothing else in Coco needs to change.

## Going further

- COT parsing (`cot_sentiment.py`) ships with a safe neutral
  placeholder — wire in a real CFTC CSV parser when ready
- Retail sentiment ships neutral too — swap in OANDA/FXSSI
  once you have those API credentials
- SMC pattern detection (order blocks, FVGs) can slot into
  `technical_signal.py`'s technical engine following the same
  `{"direction", "strength", "reasons"}` shape every other
  engine uses
- For 24/7 hosting (not just your laptop), deploy `main.py`
  to Railway.app's free tier when you're ready — the code is
  written to run anywhere Python runs, no changes needed


## Security

Never commit `.env`, API keys, Telegram bot tokens, database files, virtual environments, or runtime logs. If a credential is ever exposed, revoke/rotate it immediately and replace it in your local environment.

## Risk Disclaimer

This software generates market/forex trading signals for research and educational purposes. It does not guarantee profits or future market performance and is not financial advice. Trading leveraged instruments can result in substantial losses. Validate signals independently and use appropriate risk controls.
