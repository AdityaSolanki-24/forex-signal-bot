"""
Coco OS — Telegram Sender  (Layer K)
========================================
Sends formatted Coco messages to your Telegram chat.

Every API call is wrapped in error handling so that one
failed request never crashes the whole system — it just
prints a warning and continues.
"""

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_to_telegram(message):
    """
    Send a text message to your Telegram chat.
    Returns True on success, False on failure.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True

        print(f"  ! Telegram error {response.status_code}: {response.text}")
        return False

    except requests.RequestException as e:
        print(f"  ! Telegram connection error: {e}")
        return False
