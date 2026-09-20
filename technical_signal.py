"""
Coco OS — Technical Signal Cycle  (ties engines C + risk together)
=========================================================================
Runs the continuous 5-minute confluence check across every
forex pair: combines institutional bias, social sentiment,
and risk environment into one pair-level decision, then
sends through coco_engine + coco_format if it clears the
confidence threshold.

News-driven signals (news_engine.py) and VIP/whale signals
(vip_monitor.py / whale_alert.py) are handled separately —
this file is specifically the "nothing special happened, but
do the numbers still line up" continuous scan.
"""

from config import FOREX_SYMBOLS
from cot_sentiment import institutional_signal
from social_engine import social_signal
from risk_environment import get_vix, risk_environment_adjustment, check_black_swan
from coco_engine import combine_signals, passes_threshold, calculate_pip_target
from coco_format import format_signal
from telegram_bot import send_to_telegram
from database import log_signal

# Default base pip range for pure technical signals (no
# news/event driving them) — smaller than a news surprise.
TECHNICAL_BASE_PIPS = (20, 50)

_pair_to_social_symbols = {
    "EUR/USD": ("EURUSD", "EUR"),
    "GBP/USD": ("GBPUSD", "GBP"),
    "USD/JPY": ("USDJPY", "JPY"),
    "AUD/USD": ("AUDUSD", "AUD"),
    "USD/CAD": ("USDCAD", "CAD"),
    "USD/CHF": ("USDCHF", "CHF"),
    "NZD/USD": ("NZDUSD", "NZD"),
}

_no_engine_vote = {"direction": "NEUTRAL", "strength": 0, "reasons": []}


def _currencies_for_pair(pair):
    base, quote = pair.split("/")
    return base, quote


def run_technical_cycle():
    """
    Called periodically from main.py. Runs the full
    confluence check for every forex pair and sends any
    signal that clears the threshold.
    """
    if check_black_swan():
        message = (
            "🚨 COCO — BLACK SWAN DETECTED\n\n"
            "VIX has spiked sharply in the last hour.\n"
            "All technical signals suspended until volatility\n"
            "stabilizes. Trade manually with extra caution."
        )
        send_to_telegram(message)
        print("  ! Black swan detected — technical cycle skipped.")
        return

    vix = get_vix()

    for pair in FOREX_SYMBOLS:
        base, quote = _currencies_for_pair(pair)
        social_symbol, reddit_keyword = _pair_to_social_symbols.get(pair, (pair.replace("/", ""), base))

        institutional = institutional_signal(pair, base, quote)
        social = social_signal(social_symbol, reddit_keyword)

        # Technical engine here is intentionally simple in
        # Phase 1: it carries the risk-environment vote.
        # SMC pattern detection (order blocks/FVGs) is a
        # natural next addition — slot it in here later
        # following the exact same {"direction", "strength",
        # "reasons"} shape.
        risk_adjustment, risk_reason = risk_environment_adjustment(pair, vix)
        technical = {
            "direction": "NEUTRAL",
            "strength": 0,
            "reasons": [risk_reason] if risk_reason else [],
        }
        if risk_adjustment > 0:
            technical["direction"] = "BUY"
            technical["strength"] = min(10, risk_adjustment)
        elif risk_adjustment < 0:
            technical["direction"] = "SELL"
            technical["strength"] = min(10, abs(risk_adjustment))

        result = combine_signals(
            institutional=institutional,
            news=_no_engine_vote,   # news engine handles its own signals separately
            social=social,
            technical=technical,
        )

        if not passes_threshold(result):
            continue

        pip_low, pip_high, stop_loss_pips = calculate_pip_target(
            result["confidence"], TECHNICAL_BASE_PIPS
        )

        message = format_signal(
            pair=pair,
            direction=result["direction"],
            confidence=result["confidence"],
            pip_low=pip_low,
            pip_high=pip_high,
            stop_loss_pips=stop_loss_pips,
            reasons=result["reasons"][:4],  # keep the message readable
            source_tag="TECHNICAL",
        )

        if send_to_telegram(message):
            print(f"  > Technical signal sent: {pair} {result['direction']} ({result['confidence']}%)")
            log_signal(
                pair=pair, direction=result["direction"], confidence=result["confidence"],
                source_tag="TECHNICAL", pip_low=pip_low, pip_high=pip_high,
                stop_loss_pips=stop_loss_pips, reasons=result["reasons"],
            )
