"""
Coco — Calendar Debug Test
Run this to see exactly what events Coco can detect.
"""
import sys
sys.path.insert(0, '.')

from econ_calendar import get_calendar_events, get_upcoming_high_impact, get_just_released

print("=" * 50)
print("COCO CALENDAR DEBUG TEST")
print("=" * 50)

# Load all events
events = get_calendar_events()
print(f"\nTotal events loaded: {len(events)}")

# High impact only
high = [e for e in events if e.get("impact") == "High"]
print(f"High impact events: {len(high)}")

print("\nAll HIGH impact events this week:")
for e in high[:15]:
    title = e.get("title", "?")
    date = e.get("date", "?")
    actual = e.get("actual", "")
    forecast = e.get("forecast", "")
    print(f"  {date} | {title} | forecast: {forecast} | actual: {actual}")

# Check upcoming in next 2 hours
print("\nUpcoming HIGH impact in next 2 hours:")
upcoming = get_upcoming_high_impact(minutes_ahead=120)
if upcoming:
    for e in upcoming:
        print(f"  FOUND: {e.get('title')} at {e.get('date')}")
else:
    print("  None within 2 hours right now")

# Check just released
print("\nJust released in last 10 minutes:")
released = get_just_released(minutes_window=10)
if released:
    for e in released:
        print(f"  RELEASED: {e.get('title')} | actual: {e.get('actual')}")
else:
    print("  None released in last 10 minutes")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
