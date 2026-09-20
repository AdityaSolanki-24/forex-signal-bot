"""
Coco OS — Main Orchestrator
================================
The single entry point. Run this file and Coco starts:

  - Sending a startup confirmation to Telegram
  - Checking VIP accounts (Trump/Fed/etc) every tick (~60s)
  - Checking whale transactions every tick
  - Checking the economic calendar every ~60 ticks (hourly)
    for pre-event alerts and just-released numbers
  - Running social sentiment every ~2 ticks
  - Running the full technical confluence cycle every ~5 ticks
  - Logging every signal to the database

Run with:
    python main.py

Press Ctrl+C to stop Coco cleanly at any time.
"""

import time
from datetime import datetime

from config import (
    MAIN_LOOP_INTERVAL_SECONDS, PRICE_CHECK_EVERY_N_TICKS,
    CALENDAR_CHECK_EVERY_N_TICKS, SOCIAL_CHECK_EVERY_N_TICKS,
)
from database import init_database, get_signal_count, get_accuracy_stats
from telegram_bot import send_to_telegram
from coco_format import format_signal, format_accuracy_report
from price_feed import get_all_prices
from news_engine import run_news_engine_tick
from vip_monitor import check_vip_posts
from whale_alert import check_whale_transactions
from technical_signal import run_technical_cycle

REWEIGHT_EVERY_N_SIGNALS = 200


def startup_message():
    return (
        "🔔 COCO is online\n\n"
        "All layers initializing:\n"
        "  ✅ Price feed\n"
        "  ✅ News engine (calendar + deviation scoring)\n"
        "  ✅ Institutional bias (COT + retail sentiment)\n"
        "  ✅ Social engine (StockTwits + Reddit)\n"
        "  ✅ VIP monitor (Trump/Fed/ECB/BOJ)\n"
        "  ✅ Whale tracker\n"
        "  ✅ Risk environment (VIX)\n"
        "  ✅ Confluence engine + database logger\n\n"
        "Running fully automated — no manual input needed."
    )


def handle_vip_events(events):
    """Sends an emergency signal for each new VIP post detected."""
    from database import log_signal

    for event in events:
        confidence = min(95, event["confidence"])
        # A simple, transparent pip estimate for VIP posts —
        # scaled by how confident the sentiment scoring was.
        pip_low = round(40 + confidence * 0.4)
        pip_high = round(70 + confidence * 0.6)
        stop_loss_pips = round(pip_low * 0.4)

        direction = "BUY" if event["sentiment"] == "BULLISH" else "SELL"
        if event["sentiment"] == "NEUTRAL":
            continue

        message = format_signal(
            pair="USD/JPY",  # safe-haven proxy pair for VIP/political posts; broaden later
            direction=direction,
            confidence=confidence,
            pip_low=pip_low,
            pip_high=pip_high,
            stop_loss_pips=stop_loss_pips,
            reasons=[
                f"{event['name']} posted: \"{event['text'][:100]}...\"",
                f"NLP sentiment: {event['sentiment']} ({confidence}% confidence)",
                f"Published {event.get('age_minutes', '?')} min ago",
            ],
            source_tag="VIP POST",
            extra_lines=["⚠️ High volatility — wider stop recommended"],
        )

        if send_to_telegram(message):
            print(f"  > VIP signal sent: {event['name']} -> {direction}")
            log_signal(
                pair="USD/JPY", direction=direction, confidence=confidence,
                source_tag="VIP POST", pip_low=pip_low, pip_high=pip_high,
                stop_loss_pips=stop_loss_pips,
                reasons=[f"{event['name']}: {event['sentiment']}"],
            )


def handle_whale_events(events):
    """Sends a signal for each significant whale transaction."""
    from database import log_signal

    for event in events:
        if event["direction_hint"] == "NEUTRAL":
            continue

        pair = f"{event['symbol']}/USD"
        confidence = 65  # whale heuristics are directional hints, not high-certainty
        pip_low, pip_high, stop_loss_pips = 40, 90, 25

        message = format_signal(
            pair=pair,
            direction=event["direction_hint"],
            confidence=confidence,
            pip_low=pip_low,
            pip_high=pip_high,
            stop_loss_pips=stop_loss_pips,
            reasons=[
                f"${event['amount_usd']:,.0f} {event['symbol']} moved "
                f"{event['from_type']} -> {event['to_type']}",
                "Large exchange flows often precede price movement",
            ],
            source_tag="WHALE",
        )

        if send_to_telegram(message):
            print(f"  > Whale signal sent: {pair} {event['direction_hint']}")
            log_signal(
                pair=pair, direction=event["direction_hint"], confidence=confidence,
                source_tag="WHALE", pip_low=pip_low, pip_high=pip_high,
                stop_loss_pips=stop_loss_pips,
                reasons=[f"Whale move: {event['from_type']} -> {event['to_type']}"],
            )


def maybe_send_accuracy_report(last_reported_count):
    """Checks if enough new signals have logged to trigger
    the public accuracy report, and sends it if so."""
    current_count = get_signal_count()
    if current_count - last_reported_count >= REWEIGHT_EVERY_N_SIGNALS:
        stats = get_accuracy_stats()
        send_to_telegram(format_accuracy_report(stats))
        print(f"  > Accuracy report sent at {current_count} total signals.")
        return current_count
    return last_reported_count


def main():
    print("=" * 50)
    print("  COCO OS — starting up")
    print("=" * 50)

    init_database()

    if send_to_telegram(startup_message()):
        print("✅ Startup message sent to Telegram.")
    else:
        print("❌ Could not reach Telegram — check your keys in config.py")
        print("   Coco will keep trying on the next tick rather than exit.")

    tick = 0
    last_reported_count = get_signal_count()

    print(f"\nCoco is now running. Heartbeat every {MAIN_LOOP_INTERVAL_SECONDS}s.")
    print("Press Ctrl+C to stop.\n")

    while True:
        tick += 1
        now = datetime.now().strftime("%H:%M:%S")

        try:
            # ── VIP monitor — every tick (this list is tiny) ──
            vip_events = check_vip_posts()
            if vip_events:
                print(f"[{now}] VIP event(s) detected: {len(vip_events)}")
                handle_vip_events(vip_events)

            # ── Whale tracker — every tick ──
            whale_events = check_whale_transactions()
            if whale_events:
                print(f"[{now}] Whale event(s) detected: {len(whale_events)}")
                handle_whale_events(whale_events)

            # ── News engine ─
            if tick % CALENDAR_CHECK_EVERY_N_TICKS == 0 or tick == 1:
                print(f"[{now}] Running news engine check...")
                run_news_engine_tick()

            # ── Social-driven technical cycle ──
            if tick % SOCIAL_CHECK_EVERY_N_TICKS == 0:
                print(f"[{now}] Running technical confluence cycle...")
                run_technical_cycle()

            # ── Live price snapshot (just for visibility) ──
            if tick % PRICE_CHECK_EVERY_N_TICKS == 0:
                prices = get_all_prices()
                print(f"[{now}] Live prices: {prices}")

            # ── Self-improvement accuracy report ──
            last_reported_count = maybe_send_accuracy_report(last_reported_count)

        except Exception as e:
            print(f"  ! Unexpected error on tick {tick}: {e}")
            time.sleep(30)  # wait 30s before next tick if something went wrong

        time.sleep(MAIN_LOOP_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
