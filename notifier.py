"""
Notifiche Telegram — invia ogni nuovo annuncio come messaggio
"""
import os
import httpx
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def send_message(text: str, parse_mode: str = "HTML") -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram non configurato — imposta TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
        return False
    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN, method="sendMessage")
    try:
        resp = httpx.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def send_photo(image_url: str, caption: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN, method="sendPhoto")
    try:
        resp = httpx.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"sendPhoto fallback to text: {e}")
        return False

def format_listing(listing: dict) -> str:
    flag  = listing.get("country_flag", "")
    country = listing.get("country", "")
    site  = listing.get("site", "")
    title = listing.get("title", "Senza titolo")
    price = listing.get("price") or "Prezzo non indicato"
    url   = listing.get("url", "")
    return (
        f"{flag} <b>{country}</b> — {site}\n"
        f"📦 {title}\n"
        f"💶 {price}\n"
        f"🔗 <a href='{url}'>Vedi annuncio</a>"
    )

def send_telegram_batch(listings: list):
    """Invia un messaggio Telegram per ogni nuovo annuncio."""
    for listing in listings:
        caption = format_listing(listing)
        img = listing.get("image_url")
        if img:
            ok = send_photo(img, caption)
            if not ok:
                send_message(caption)
        else:
            send_message(caption)
