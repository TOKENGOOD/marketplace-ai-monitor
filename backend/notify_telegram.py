import os, requests

BOT = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_CHAT = os.getenv("TELEGRAM_CHAT_ID")

def send_item(item, profile):
    """Send a Telegram message.
    Returns:
      True  -> sent successfully
      False -> API call attempted but failed
      None  -> not configured (missing token or chat)
    """
    token = BOT
    chat = profile.get("chat_id") or DEFAULT_CHAT
    if not token or not chat:
        # Not configured
        return None

    price = item.get("price_cents", 0) / 100
    text = (
        f"✅ [{profile.get('name')}] Match\n"
        f"{item.get('title')}\n"
        f"Price: £{price:.2f}\n"
        f"Score: {item.get('score'):.2f} — {item.get('reason')}\n"
        f"{item.get('url')}"
    )
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
            "chat_id": chat,
            "text": text,
            "disable_web_page_preview": True
        }, timeout=20)
        # Consider success only if HTTP OK and Telegram says ok=true
        if r.ok:
            try:
                data = r.json()
                return bool(data.get("ok", False))
            except Exception:
                # If JSON parse fails but HTTP 200, count as success
                return True
        return False
    except Exception as e:
        print("Telegram send error:", e)
        return False
