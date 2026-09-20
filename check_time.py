"""
Coco — Timezone Check
Run: python check_time.py
"""
from datetime import datetime

now = datetime.now().astimezone()
print("=" * 40)
print("YOUR SYSTEM TIME CHECK")
print("=" * 40)
print(f"Local time:  {now.strftime('%H:%M:%S')}")
print(f"Date:        {now.strftime('%Y-%m-%d')}")
print(f"Timezone:    {now.strftime('%Z')}")
print(f"UTC offset:  {now.strftime('%z')}")
print()

# NFP time
from datetime import timezone, timedelta
nfp_et = datetime(2026, 7, 2, 8, 30, 0,
                  tzinfo=timezone(timedelta(hours=-4)))
nfp_local = nfp_et.astimezone()
print(f"NFP release (ET):    08:30 AM ET")
print(f"NFP release (local): {nfp_local.strftime('%H:%M %Z')}")

diff = nfp_local - now
minutes = int(diff.total_seconds() / 60)
if minutes > 0:
    print(f"NFP in:      {minutes} minutes")
    print(f"Pre-alert:   {(nfp_local - timedelta(minutes=30)).strftime('%H:%M')} local time")
else:
    print(f"NFP already passed {abs(minutes)} minutes ago")
print("=" * 40)
