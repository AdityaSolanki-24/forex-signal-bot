"""
Coco OS — Signal Formatter
============================
Builds the standard Coco signal message used by EVERY
engine: news, VIP/social posts, whale moves, and technical
signals all funnel through this one function.

Format = data-first, with light Coco branding in the header.
Every signal includes:
  - Pair + direction (BUY / SELL)
  - Confidence % with a visual bar
  - Pip target as a RANGE (e.g. 55-85 pips)
  - A suggested stop-loss in pips
  - The top reasons behind the signal
"""

from config import HIGH_CONFIDENCE_THRESHOLD


def confidence_bar(confidence):
    """
    Turn a 0-100 confidence score into a visual bar,
    e.g. confidence_bar(72) -> '███████░░░'
    """
    filled = int(confidence / 10)
    filled = max(0, min(10, filled))
    return "█" * filled + "░" * (10 - filled)


def format_signal(
    pair,
    direction,            # "BUY" or "SELL"
    confidence,           # 0-100
    pip_low,              # lower end of pip target range
    pip_high,             # upper end of pip target range
    stop_loss_pips,       # suggested stop-loss size in pips
    reasons,              # list of short strings
    source_tag="TECHNICAL",   # "NEWS", "VIP POST", "WHALE", "TECHNICAL", "EXAMPLE"
    extra_lines=None,     # optional list of extra strings (timing, warnings, etc.)
    delivery_seconds=None,  # how long detection-to-delivery took, if known
):
    """
    Build the full Coco signal message as a string,
    ready to send straight to Telegram.
    """
    arrow = "⬆️" if direction.upper() == "BUY" else "⬇️"
    bar = confidence_bar(confidence)

    header_tag = source_tag
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        header_tag = f"{source_tag} · HIGH CONFIDENCE"

    reasons_block = "\n".join(f"  • {r}" for r in reasons)

    extra_block = ""
    if extra_lines:
        extra_block = "\n" + "\n".join(extra_lines)

    timing_line = ""
    if delivery_seconds is not None:
        timing_line = f"\n⏱ Delivered {delivery_seconds}s after detection"

    message = (
        f"🔔 COCO SIGNAL — {header_tag}\n\n"
        f"{arrow} {pair} — {direction.upper()}\n"
        f"Confidence: {bar} {confidence}%\n\n"
        f"🎯 Target: {pip_low}\u2013{pip_high} pips\n"
        f"🛑 Stop-loss: {stop_loss_pips} pips\n\n"
        f"Reasons:\n{reasons_block}"
        f"{extra_block}"
        f"{timing_line}"
    )
    return message


def format_no_trade(pair, reason):
    """A quiet, low-noise message for the rare case you want
    visibility into why Coco stayed silent on something."""
    return f"➡️ COCO — {pair} — NO SIGNAL\n\n{reason}"


def format_health_report(api_status, signals_yesterday, accuracy_7d, errors_overnight, calendar_today):
    """Daily 07:00 GMT health check message."""
    status_lines = "\n".join(f"  {name}: {status}" for name, status in api_status.items())
    calendar_lines = "\n".join(f"  • {event}" for event in calendar_today) if calendar_today else "  (none scheduled)"

    return (
        f"🔧 COCO DAILY HEALTH CHECK\n\n"
        f"API status:\n{status_lines}\n\n"
        f"Signals sent yesterday: {signals_yesterday}\n"
        f"7-day accuracy: {accuracy_7d}%\n"
        f"Errors overnight: {errors_overnight}\n\n"
        f"Today's calendar:\n{calendar_lines}"
    )


def format_accuracy_report(stats):
    """Public accuracy report sent every REWEIGHT_EVERY_N_SIGNALS."""
    return (
        f"📊 COCO ACCURACY REPORT\n\n"
        f"Signals scored: {stats['total_scored']}\n"
        f"Wins: {stats['wins']}\n"
        f"Win rate: {stats['win_rate']}%\n\n"
        f"This report is generated automatically from\n"
        f"logged outcomes — see database.py"
    )
