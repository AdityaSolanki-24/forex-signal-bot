"""
Coco — Upcoming Events Test
Run: python check_events.py
"""
import sys
sys.path.insert(0, '.')

from econ_calendar import get_upcoming_high_impact, get_calendar_events

print("=" * 50)
print("EVENTS IN NEXT 6 HOURS")
print("=" * 50)

upcoming = get_upcoming_high_impact(minutes_ahead=360)
print(f"Found: {len(upcoming)} events")
for e in upcoming:
    print(f"  {e.get('date')} | {e.get('title')} | forecast: {e.get('forecast')}")

print("\nALL HIGH IMPACT THIS WEEK:")
events = get_calendar_events()
high = [e for e in events if e.get("impact") == "High"]
for e in high:
    print(f"  {e.get('date')} | {e.get('title')} | actual: {e.get('actual')}")

print("=" * 50)
