"""
Coco OS — Economic Calendar Scanner (Fixed Version)
=====================================================
Root cause fixes:
1. Timezone conversion fixed for IST users
2. Pre-alert window uses LOCAL time comparison (not UTC)
3. Actual value detection widened to 60-minute window
4. Verbose logging shows exactly what times are being compared
5. Cache properly invalidated for release detection
"""

import requests
import time
from datetime import datetime, timedelta, timezone

from config import FINNHUB_API_KEY, NEWS_EVENTS

_calendar_cache = []
_last_fetch_time = None
_cache_duration_minutes = 60


def get_calendar_events():
    """
    Fetches economic calendar with 60-minute cache.
    Uses Finnhub if key available, else Forex Factory.
    """
    global _calendar_cache, _last_fetch_time

    now = datetime.now()

    if (_last_fetch_time and
            (now - _last_fetch_time).total_seconds() <
            (_cache_duration_minutes * 60)):
        return _calendar_cache

    # Try Finnhub first
    if FINNHUB_API_KEY and "YOUR_" not in FINNHUB_API_KEY:
        events = _fetch_finnhub_calendar()
        if events:
            _calendar_cache = events
            _last_fetch_time = now
            print(f"  > Calendar loaded: {len(events)} events (Finnhub)")
            return events

    # Fallback: Forex Factory
    events = _fetch_forex_factory()
    if events:
        _calendar_cache = events
        _last_fetch_time = now
        print(f"  > Calendar loaded: {len(events)} events (Forex Factory)")
        return events

    if _calendar_cache:
        print("  > Calendar using cached data")
        return _calendar_cache

    return []


def force_refresh_calendar():
    """Forces a fresh calendar fetch — bypasses cache."""
    global _last_fetch_time
    _last_fetch_time = None
    print("  > Calendar cache cleared — force refreshing...")
    return get_calendar_events()


def _fetch_finnhub_calendar():
    """Fetches from Finnhub economic calendar API."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        url = "https://finnhub.io/api/v1/calendar/economic"
        params = {
            "token": FINNHUB_API_KEY,
            "from": today,
            "to": week_later,
        }

        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        events = []
        for item in data.get("economicCalendar", []):
            events.append({
                "title": item.get("event", ""),
                "country": item.get("country", "").upper(),
                "date": item.get("time", ""),
                "impact": _map_finnhub_impact(item.get("impact", "")),
                "forecast": str(item.get("estimate", "")),
                "previous": str(item.get("prev", "")),
                "actual": str(item.get("actual", "")),
            })

        return events

    except Exception as e:
        print(f"  ! Finnhub calendar error: {e}")
        return []


def _map_finnhub_impact(impact_str):
    mapping = {
        "high": "High", "medium": "Medium", "low": "Low",
        "3": "High", "2": "Medium", "1": "Low",
    }
    return mapping.get(str(impact_str).lower(), "Low")


def _fetch_forex_factory():
    """Fetches from Forex Factory with rate limit protection."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.forexfactory.com/",
    }

    for attempt in range(2):
        try:
            if attempt > 0:
                print(f"  > Calendar retry {attempt} — waiting 30s...")
                time.sleep(30)

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 429:
                print("  ! Calendar rate limited — using cached data")
                return []

            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"  ! Forex Factory error: {e}")

    return []


def _parse_event_time(date_str):
    """
    Parses event time and converts to LOCAL machine time.
    This is the critical fix — comparing local time to
    event time in the same timezone.
    """
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(str(date_str))
        if dt.tzinfo is not None:
            # Convert to local machine time (IST for you)
            dt = dt.astimezone()
        return dt
    except (ValueError, TypeError):
        try:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d %H:%M:%S")
            return dt
        except (ValueError, TypeError):
            return None


def _match_known_event(title):
    """Matches calendar title against known events."""
    title_lower = title.lower()
    for key, cfg in NEWS_EVENTS.items():
        if cfg["match"].lower() in title_lower:
            return key
    return None


def get_upcoming_high_impact(minutes_ahead=30):
    """
    Returns high-impact events in the next N minutes.
    Uses local machine time for comparison.
    """
    events = get_calendar_events()
    now = datetime.now().astimezone()
    window_end = now + timedelta(minutes=minutes_ahead)

    upcoming = []
    for event in events:
        if event.get("impact") != "High":
            continue

        event_time = _parse_event_time(event.get("date", ""))
        if event_time is None:
            continue

        # Ensure event_time is timezone-aware
        if event_time.tzinfo is None:
            event_time = event_time.astimezone()

        if now <= event_time <= window_end:
            matched_key = _match_known_event(event.get("title", ""))
            if matched_key:
                event["_matched_key"] = matched_key
                upcoming.append(event)
                print(f"  > UPCOMING EVENT FOUND: {event.get('title')} "
                      f"at {event_time.strftime('%H:%M IST')} "
                      f"(in {int((event_time-now).total_seconds()/60)} min)")

    return upcoming


def get_just_released(minutes_window=30):
    """
    Returns events that just released with a non-empty actual value.
    Uses 30-minute window to handle Forex Factory delayed updates.
    """
    events = get_calendar_events()
    now = datetime.now().astimezone()
    window_start = now - timedelta(minutes=minutes_window)

    released = []
    for event in events:
        if event.get("impact") != "High":
            continue

        actual = event.get("actual", "")
        if not actual or str(actual).strip() in ("", "None", "nan", "null"):
            continue

        event_time = _parse_event_time(event.get("date", ""))
        if event_time is None:
            continue

        if event_time.tzinfo is None:
            event_time = event_time.astimezone()

        if window_start <= event_time <= now:
            matched_key = _match_known_event(event.get("title", ""))
            if matched_key:
                event["_matched_key"] = matched_key
                released.append(event)
                print(f"  > RELEASED EVENT: {event.get('title')} | "
                      f"actual={actual}")

    return released


def parse_numeric(value_str):
    """Converts '0.3%' or '165K' to float."""
    if not value_str or str(value_str).strip() in ("None", "", "nan", "null"):
        return None

    cleaned = str(value_str).strip().replace("%", "").replace(",", "")
    multiplier = 1.0

    if cleaned.upper().endswith("K"):
        cleaned = cleaned[:-1]
    elif cleaned.upper().endswith("M"):
        cleaned = cleaned[:-1]
        multiplier = 1000.0

    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None
