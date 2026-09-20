"""
Coco OS — News Engine (Fixed Version)
=========================================
Root cause fixes:
1. Pre-event alerts now use broader time matching
2. Release detection widened to 30-minute window
3. Timezone handling fixed for IST users
4. All Forex Factory actual values properly parsed
5. Added verbose logging so you can see exactly
   what the engine is checking every tick
"""

from datetime import datetime
from config import NEWS_EVENTS, PRE_EVENT_ALERT_MINUTES_BEFORE
from econ_calendar import (
    get_upcoming_high_impact,
    get_just_released,
    parse_numeric,
    force_refresh_calendar,
)
from coco_format import format_signal
from telegram_bot import send_to_telegram
from database import log_signal

_pre_alerted = set()
_signalled = set()


def _event_key(event):
    return f"{event.get('title', '')}|{event.get('date', '')}"


def _direction_for_pair(pair_rule, currency_stronger):
    if pair_rule == "direct":
        return "BUY" if currency_stronger else "SELL"
    else:
        return "SELL" if currency_stronger else "BUY"


def check_pre_event_alerts():
    """
    Sends pre-event alert 30 minutes before any matched
    high-impact release. Verbose logging shows exactly
    what is being checked.
    """
    upcoming = get_upcoming_high_impact(
        minutes_ahead=PRE_EVENT_ALERT_MINUTES_BEFORE
    )

    print(f"  > Pre-event check: {len(upcoming)} events within "
          f"{PRE_EVENT_ALERT_MINUTES_BEFORE} min window")

    for event in upcoming:
        key = _event_key(event)
        if key in _pre_alerted:
            print(f"  > Pre-alert already sent for: {event.get('title')}")
            continue

        event_cfg = NEWS_EVENTS[event["_matched_key"]]
        forecast = event.get("forecast", "n/a")
        previous = event.get("previous", "n/a")
        pip_low, pip_high = event_cfg["base_pips"]

        message = (
            f"⏰ COCO PRE-EVENT ALERT\n\n"
            f"📅 {event.get('title')}\n"
            f"💱 Currency: {event_cfg['currency']}\n"
            f"📊 Forecast: {forecast} | Previous: {previous}\n\n"
            f"📈 IF BEATS forecast:\n"
            f"   {event_cfg['currency']} strengthens → "
            f"{pip_low}–{pip_high} pip move\n"
            f"📉 IF MISSES forecast:\n"
            f"   {event_cfg['currency']} weakens → "
            f"{pip_low}–{pip_high} pip move\n"
            f"➡️ IF IN LINE: small reaction expected\n\n"
            f"⚠️ Signal fires within 2 seconds of release."
        )

        if send_to_telegram(message):
            print(f"  > ✅ Pre-event alert sent: {event.get('title')}")
            _pre_alerted.add(key)
        else:
            print(f"  > ❌ Pre-event alert FAILED to send: {event.get('title')}")


def check_releases_and_signal():
    """
    Detects events that just released and sends
    the main BUY/SELL signal. Uses 30-minute window
    to handle Forex Factory delayed actual updates.
    Verbose logging shows every check.
    """
    # Force refresh to get latest actual values
    force_refresh_calendar()
    released = get_just_released(minutes_window=30)

    print(f"  > Release check: {len(released)} events just released")

    for event in released:
        key = _event_key(event)
        if key in _signalled:
            print(f"  > Signal already sent for: {event.get('title')}")
            continue

        actual = parse_numeric(event.get("actual"))
        forecast = parse_numeric(event.get("forecast"))

        print(f"  > Processing: {event.get('title')} | "
              f"actual={event.get('actual')} forecast={event.get('forecast')}")

        if actual is None or forecast is None:
            print(f"  > Skipping — cannot parse numbers for {event.get('title')}")
            _signalled.add(key)
            continue

        event_cfg = NEWS_EVENTS[event["_matched_key"]]
        deviation = actual - forecast
        typical_dev = event_cfg["typical_deviation"]

        if typical_dev == 0:
            _signalled.add(key)
            continue

        significance = abs(deviation) / typical_dev
        currency_stronger = deviation > 0

        print(f"  > Deviation: {deviation:.3f} | "
              f"Significance: {significance:.1f}x | "
              f"Currency stronger: {currency_stronger}")

        if significance < 0.5:
            print(f"  > In-line result — no signal generated")
            _signalled.add(key)
            continue

        confidence = min(90, int(50 + significance * 20))
        scale = min(2.0, max(0.5, significance))
        pip_low_base, pip_high_base = event_cfg["base_pips"]
        pip_low = round(pip_low_base * scale)
        pip_high = round(pip_high_base * scale)
        stop_loss_pips = round(pip_low * 0.5)

        for pair, rule in event_cfg["pairs"].items():
            direction = _direction_for_pair(rule, currency_stronger)

            reasons = [
                f"{event.get('title')}: actual {event.get('actual')} "
                f"vs forecast {event.get('forecast')}",
                f"Deviation: {significance:.1f}x typical surprise",
            ]
            if significance >= 1.5:
                reasons.append(
                    "Large surprise — historically produces sustained moves"
                )

            message = format_signal(
                pair=pair,
                direction=direction,
                confidence=confidence,
                pip_low=pip_low,
                pip_high=pip_high,
                stop_loss_pips=stop_loss_pips,
                reasons=reasons,
                source_tag="NEWS",
                extra_lines=["🔄 Reversal check in 5 minutes"],
            )

            if send_to_telegram(message):
                print(f"  > ✅ NEWS signal sent: {pair} {direction} "
                      f"({confidence}%) — {event.get('title')}")
                log_signal(
                    pair=pair,
                    direction=direction,
                    confidence=confidence,
                    source_tag="NEWS",
                    pip_low=pip_low,
                    pip_high=pip_high,
                    stop_loss_pips=stop_loss_pips,
                    reasons=reasons,
                )
            else:
                print(f"  > ❌ NEWS signal FAILED to send for {pair}")

        _signalled.add(key)


def run_news_engine_tick():
    """Called every tick from main.py."""
    check_pre_event_alerts()
    check_releases_and_signal()
