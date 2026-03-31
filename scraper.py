"""
Subbuteo Scraper — raschia i principali siti di annunci secondari per paese
Paesi: SE, FI, PT, DK, BR, ES, DE, FR, CH, AT, NL, BE
"""
import hashlib
import re
import time
import random
import logging
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

KEYWORDS = ["subbuteo", "subbut", "subboteo", "subbutéo", "subbueto"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def keyword_match(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in KEYWORDS)

def get(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.warning(f"GET {url} → {e}")
        return None

# ---------------------------------------------------------------------------
# SVEZIA — Blocket.se
# ---------------------------------------------------------------------------
def scrape_blocket():
    results = []
    url = "https://www.blocket.se/annonser/hela_sverige?q=subbuteo&ca=0&cg=0&w=3"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article[data-testid='list-item']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.blocket.se" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Blocket.se",
            "country": "Svezia",
            "country_flag": "🇸🇪",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# FINLANDIA — Tori.fi
# ---------------------------------------------------------------------------
def scrape_tori():
    results = []
    url = "https://www.tori.fi/koko_suomi?q=subbuteo&cg=0&w=3&o=1"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article.item_row, .list_item, [class*='item']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.tori.fi" + href
        title_el = card.select_one("h2,h3,h4,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Tori.fi",
            "country": "Finlandia",
            "country_flag": "🇫🇮",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# PORTOGALLO — OLX.pt
# ---------------------------------------------------------------------------
def scrape_olx_pt():
    results = []
    url = "https://www.olx.pt/ads/q-subbuteo/"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("[data-cy='l-card'], .offer-wrapper, article"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.olx.pt" + href
        title_el = card.select_one("h3,h4,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[data-testid='ad-price'], [class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "OLX.pt",
            "country": "Portogallo",
            "country_flag": "🇵🇹",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# DANIMARCA — DBA.dk
# ---------------------------------------------------------------------------
def scrape_dba():
    results = []
    url = "https://www.dba.dk/soeg/?soeg=subbuteo"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select(".listingLink, .item, article, [class*='listing']"):
        a = card if card.name == "a" else card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.dba.dk" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "DBA.dk",
            "country": "Danimarca",
            "country_flag": "🇩🇰",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# BRASILE — OLX.com.br
# ---------------------------------------------------------------------------
def scrape_olx_br():
    results = []
    url = "https://www.olx.com.br/brasil?q=subbuteo"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("[data-lurker-detail='list_id'], article, .item"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.olx.com.br" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "OLX.br",
            "country": "Brasile",
            "country_flag": "🇧🇷",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# SPAGNA — Wallapop (API pubblica) + Milanuncios
# ---------------------------------------------------------------------------
def scrape_wallapop():
    results = []
    url = (
        "https://api.wallapop.com/api/v3/general/search"
        "?keywords=subbuteo&filters_source=search_box&order_by=newest&start=0&step=40"
    )
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        data = resp.json()
        items = data.get("data", {}).get("section", {}).get("payload", {}).get("items", [])
        for item in items:
            cnt = item.get("content", {})
            item_id = cnt.get("id") or item.get("id", "")
            title = cnt.get("title", "")
            if not keyword_match(title):
                continue
            price_val = cnt.get("price", {})
            price = f"{price_val.get('amount', '')} {price_val.get('currency', '')}".strip() if isinstance(price_val, dict) else str(price_val)
            slug = cnt.get("web_slug", item_id)
            href = f"https://es.wallapop.com/item/{slug}"
            img = None
            imgs = cnt.get("images", [])
            if imgs:
                img = imgs[0].get("medium") or imgs[0].get("original")
            results.append({
                "id": make_id(href),
                "title": title,
                "price": price,
                "url": href,
                "image_url": img,
                "site": "Wallapop",
                "country": "Spagna",
                "country_flag": "🇪🇸",
                "found_at": datetime.now().isoformat(),
            })
    except Exception as e:
        logger.warning(f"Wallapop API error: {e}")
    return results

def scrape_milanuncios():
    results = []
    url = "https://www.milanuncios.com/busqueda/?q=subbuteo&orden=date"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article.ma-AdCard, .aditem, [class*='AdCard']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.milanuncios.com" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Milanuncios",
            "country": "Spagna",
            "country_flag": "🇪🇸",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# GERMANIA — Kleinanzeigen (ex eBay Kleinanzeigen)
# ---------------------------------------------------------------------------
def scrape_kleinanzeigen():
    results = []
    url = "https://www.kleinanzeigen.de/s-subbuteo/k0"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article.aditem, li.ad-listitem, [class*='aditem']"):
        a = card.select_one("a.ellipsis, a[href*='/s-anzeige/']")
        if not a:
            a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.kleinanzeigen.de" + href
        title_el = card.select_one("h2,h3,.text-module-begin,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Kleinanzeigen.de",
            "country": "Germania",
            "country_flag": "🇩🇪",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# FRANCIA — Le Bon Coin + Videdressing
# ---------------------------------------------------------------------------
def scrape_leboncoin():
    results = []
    url = "https://www.leboncoin.fr/recherche?text=subbuteo&sort=time&order=desc"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("a[data-qa-id='aditem_container'], article, [data-test-id='ad']"):
        a = card if card.name == "a" else card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.leboncoin.fr" + href
        title_el = card.select_one("h2,h3,[data-qa-id='aditem_title'],[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[data-qa-id='aditem_price'], [class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Leboncoin.fr",
            "country": "Francia",
            "country_flag": "🇫🇷",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# SVIZZERA — Ricardo.ch + Anibis.ch
# ---------------------------------------------------------------------------
def scrape_anibis():
    results = []
    url = "https://www.anibis.ch/fr/ads?q=subbuteo&sort=date_desc"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article, .listing-item, [class*='AdCard'], li[class*='item']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.anibis.ch" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Anibis.ch",
            "country": "Svizzera",
            "country_flag": "🇨🇭",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# AUSTRIA — Willhaben.at
# ---------------------------------------------------------------------------
def scrape_willhaben():
    results = []
    url = "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?sfId=dummy&keyword=subbuteo&sort=1"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("article, [data-testid='ad-card'], [class*='adCard']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.willhaben.at" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Willhaben.at",
            "country": "Austria",
            "country_flag": "🇦🇹",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# OLANDA — Marktplaats.nl
# ---------------------------------------------------------------------------
def scrape_marktplaats():
    results = []
    url = "https://www.marktplaats.nl/q/subbuteo/#sortBy:SORT_INDEX|sortOrder:DECREASING"
    soup = get(url)
    if not soup:
        return results
    for card in soup.select("li.mp-Listing, article, [class*='listing']"):
        a = card.select_one("a[href]")
        if not a:
            continue
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.marktplaats.nl" + href
        title_el = card.select_one("h2,h3,[class*='title']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not keyword_match(title + href):
            continue
        price_el = card.select_one("[class*='price']")
        price = price_el.get_text(strip=True) if price_el else None
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        results.append({
            "id": make_id(href),
            "title": title,
            "price": price,
            "url": href,
            "image_url": img,
            "site": "Marktplaats.nl",
            "country": "Olanda",
            "country_flag": "🇳🇱",
            "found_at": datetime.now().isoformat(),
        })
    return results

# ---------------------------------------------------------------------------
# BELGIO — 2ememain.be / 2dehands.be
# ---------------------------------------------------------------------------
def scrape_2ememain():
    results = []
    for base_url, site_name in [
        ("https://www.2ememain.be/q/subbuteo/", "2ememain.be"),
        ("https://www.2dehands.be/q/subbuteo/", "2dehands.be"),
    ]:
        soup = get(base_url)
        if not soup:
            continue
        for card in soup.select("article, li[class*='listing'], [class*='Listing']"):
            a = card.select_one("a[href]")
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http"):
                href = base_url.split("/q/")[0] + href
            title_el = card.select_one("h2,h3,[class*='title']")
            title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
            if not keyword_match(title + href):
                continue
            price_el = card.select_one("[class*='price']")
            price = price_el.get_text(strip=True) if price_el else None
            img_el = card.select_one("img")
            img = img_el.get("src") if img_el else None
            results.append({
                "id": make_id(href),
                "title": title,
                "price": price,
                "url": href,
                "image_url": img,
                "site": site_name,
                "country": "Belgio",
                "country_flag": "🇧🇪",
                "found_at": datetime.now().isoformat(),
            })
        time.sleep(random.uniform(1, 2))
    return results

# ---------------------------------------------------------------------------
# Runner principale
# ---------------------------------------------------------------------------

SCRAPERS = [
    ("Blocket.se 🇸🇪",       scrape_blocket),
    ("Tori.fi 🇫🇮",           scrape_tori),
    ("OLX.pt 🇵🇹",            scrape_olx_pt),
    ("DBA.dk 🇩🇰",            scrape_dba),
    ("OLX.br 🇧🇷",            scrape_olx_br),
    ("Wallapop 🇪🇸",          scrape_wallapop),
    ("Milanuncios 🇪🇸",       scrape_milanuncios),
    ("Kleinanzeigen.de 🇩🇪",  scrape_kleinanzeigen),
    ("Leboncoin.fr 🇫🇷",      scrape_leboncoin),
    ("Anibis.ch 🇨🇭",         scrape_anibis),
    ("Willhaben.at 🇦🇹",      scrape_willhaben),
    ("Marktplaats.nl 🇳🇱",    scrape_marktplaats),
    ("2ememain/2dehands 🇧🇪", scrape_2ememain),
]

class SubbuteoScraper:
    def __init__(self, db):
        self.db = db

    def run_all(self) -> int:
        """Esegue tutti gli scraper. Ritorna il numero di nuovi annunci trovati."""
        total_new = 0
        new_listings = []

        for name, fn in SCRAPERS:
            logger.info(f"Scraping {name}...")
            try:
                listings = fn()
            except Exception as e:
                logger.error(f"Errore in {name}: {e}")
                listings = []

            for listing in listings:
                if self.db.insert(listing):
                    total_new += 1
                    new_listings.append(listing)

            # pausa cortese tra i siti
            time.sleep(random.uniform(2, 4))

        self.db.log_scan(total_new, len(SCRAPERS))
        logger.info(f"Scansione completata — {total_new} nuovi annunci")

        # Notifica Telegram
        if new_listings:
            try:
                from notifier import send_telegram_batch
                send_telegram_batch(new_listings)
                for l in new_listings:
                    self.db.mark_notified(l["id"])
            except Exception as e:
                logger.error(f"Errore notifica Telegram: {e}")

        return total_new
