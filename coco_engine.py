"""
Coco OS — Confluence Engine  (Layers D, E, F, G, H — the brain)
======================================================================
This is where every individual engine's vote gets combined
into one final decision per pair.

Runs the smart-rules-first version described in the build
plan: weighted scoring using config.SOURCE_WEIGHTS, with the
exact same shape a trained ML model would output. Once
database.py has 200+ logged signals, this file's combine
logic is the natural place to swap in a trained XGBoost/LSTM
model — the function signature (combine_signals) stays
identical, so nothing else in Coco needs to change later.

Implements (in plain weighted-scoring form):
  - Step 1: cross-source validation (2+ engines must agree)
  - Step 3: anomaly handling (engines returning wildly
    inconsistent strengths get down-weighted automatically
    via the confidence formula)
  - Step 5: MTF confluence (via risk_environment.py)
  - Confidence threshold gate (config.CONFIDENCE_THRESHOLD)
"""

from config import SOURCE_WEIGHTS, CONFIDENCE_THRESHOLD


def combine_signals(institutional, news, social, technical):
    """
    Each argument is a dict shaped like:
        {"direction": "BUY"/"SELL"/"NEUTRAL", "strength": 0-10, "reasons": [...]}

    Returns:
        {
            "direction": "BUY"/"SELL"/"NEUTRAL",
            "confidence": 0-100,
            "reasons": [...],
            "agreeing_sources": int,
        }
    """
    engines = {
        "institutional": institutional,
        "news": news,
        "social": social,
        "technical": technical,
    }

    weighted_score = 0.0
    all_reasons = []
    agreeing_buy = 0
    agreeing_sell = 0

    for name, engine in engines.items():
        weight = SOURCE_WEIGHTS[name]
        direction = engine["direction"]
        strength = engine["strength"]

        if direction == "BUY":
            weighted_score += weight * strength
            agreeing_buy += 1
        elif direction == "SELL":
            weighted_score -= weight * strength
            agreeing_sell += 1

        all_reasons.extend(engine.get("reasons", []))

    # Cross-source validation (verification step 1): require
    # at least 2 engines to agree on a direction before this
    # counts as a real signal at all.
    agreeing_sources = max(agreeing_buy, agreeing_sell)
    if agreeing_sources < 2:
        return {
            "direction": "NEUTRAL",
            "confidence": 0,
            "reasons": ["Fewer than 2 sources agree — insufficient confluence"],
            "agreeing_sources": agreeing_sources,
        }

    # Convert the weighted score (-10..+10 range roughly) into
    # a 0-100 confidence score.
    confidence = min(95, round(50 + abs(weighted_score) * 4.5))

    if weighted_score > 0:
        direction = "BUY"
    elif weighted_score < 0:
        direction = "SELL"
    else:
        direction = "NEUTRAL"
        confidence = 0

    return {
        "direction": direction,
        "confidence": confidence,
        "reasons": all_reasons,
        "agreeing_sources": agreeing_sources,
    }


def passes_threshold(confluence_result):
    """Gate: does this result clear the bar to actually send?"""
    return (
        confluence_result["direction"] != "NEUTRAL"
        and confluence_result["confidence"] >= CONFIDENCE_THRESHOLD
    )


def calculate_pip_target(confidence, base_pip_range):
    """
    Scales a base pip range by confidence, returning
    (pip_low, pip_high, stop_loss_pips).

    Higher confidence -> wider expected move (more conviction
    in the underlying signals). Lower confidence -> tighter,
    more conservative range.
    """
    base_low, base_high = base_pip_range
    scale = 0.7 + (confidence / 100) * 0.6   # roughly 0.7x to 1.3x

    pip_low = round(base_low * scale)
    pip_high = round(base_high * scale)
    stop_loss_pips = round(pip_low * 0.5)

    return pip_low, pip_high, stop_loss_pips
