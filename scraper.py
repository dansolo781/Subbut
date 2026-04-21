"""
Subbuteo Scraper v3 — testato e funzionante
7 siti: Marktplaats, Finn, DBA, Kleinanzeigen, OLX.pt, 2dehands, Willhaben
"""
import httpx
from bs4 import BeautifulSoup
import json
import re
import time
import random
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

KEYWORDS = ["subbuteo", "subbut", "subboteo"]
PRICE_EUR_RE = re.compile(r"€\s*\d+(?:[.,]\d{2})?|Bieden|Gratis|Voir description", re.I)
PRICE_KR_RE  = re.compile(r"[\d.]+\s*kr\.?|Gis bort|Gives væk|Byttes", re.I)

def make_id(url): return hashlib.md5(url.encode()).hexdigest()
def match_keyword(text): return any(k in text.lower() for k in KEYWORDS)

def fetch(url):
    r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    return BeautifulSoup(r.text, "html.parser")

def text_of(card, selector):
    el = card.select_one(selector)
    return el.get_text(strip=True) if el else None

def find_by_regex(card, pattern):
    for s in card.find_all(string=pattern):
        m = pattern.search(s)
        if m: return m.group(0).strip()
    return None

def link_of(card, base="", selector="a[href]"):
    a = card.select_one(selector)
    if not a: return ""
    href = a.get("href", "")
    if href and not href.startswith("http"): href = base + href
    return href

def clean_price(raw, pattern):
    if not raw: return None
    m = pattern.search(raw)
    return m.group(0).strip() if m else raw.strip()

def make_listing(site, country, flag, title, price, url, img=None):
    return {
        "id": make_id(url),
        "site": site,
        "country": country,
        "country_flag": flag,
        "title": title,
        "price": price,
        "url": url,
        "image_url": img,
        "found_at": datetime.now().isoformat(),
    }

def scrape_marktplaats():
    out = []
    for card in fetch("https://www.marktplaats.nl/q/subbuteo/").select("li.hz-Listing"):
        title = text_of(card, "[class*='Listing-title']") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.marktplaats.nl", "a[class*='coverLink'], a[href]")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("Marktplaats.nl", "Olanda", "🇳🇱", title,
            clean_price(text_of(card, "[class*='Listing-price']"), PRICE_EUR_RE), url, img))
    return out

def scrape_finn():
    out = []
    for card in fetch("https://www.finn.no/bap/forsale/search.html?q=subbuteo").select("article"):
        title = text_of(card, "h2,h3") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.finn.no")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("Finn.no", "Norvegia", "🇳🇴", title,
            find_by_regex(card, PRICE_KR_RE), url, img))
    return out

def scrape_dba():
    out = []
    for card in fetch("https://www.dba.dk/soeg/?soeg=subbuteo").select("article"):
        title = text_of(card, "h2,h3") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.dba.dk")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("DBA.dk", "Danimarca", "🇩🇰", title,
            find_by_regex(card, PRICE_KR_RE), url, img))
    return out

def scrape_kleinanzeigen():
    out = []
    pat = re.compile(r"\d+\s*€(?:\s*VB)?|VB", re.I)
    for card in fetch("https://www.kleinanzeigen.de/s-subbuteo/k0").select("article.aditem"):
        title = text_of(card, "h2") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.kleinanzeigen.de")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("Kleinanzeigen.de", "Germania", "🇩🇪", title,
            clean_price(text_of(card, "[class*='price']"), pat), url, img))
    return out

def scrape_olx_pt():
    out = []
    for card in fetch("https://www.olx.pt/ads/q-subbuteo/").select("[data-cy='l-card']"):
        title = text_of(card, "h3,h4") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.olx.pt")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("OLX.pt", "Portogallo", "🇵🇹", title,
            text_of(card, "[data-testid='ad-price'],[class*='price']"), url, img))
    return out

def scrape_2dehands():
    out = []
    for card in fetch("https://www.2dehands.be/q/subbuteo/").select("li.hz-Listing"):
        title = text_of(card, "[class*='Listing-title']") or ""
        if not match_keyword(title): continue
        url = link_of(card, "https://www.2dehands.be", "a[class*='coverLink'], a[href]")
        img_el = card.select_one("img")
        img = img_el.get("src") if img_el else None
        out.append(make_listing("2dehands.be", "Belgio", "🇧🇪", title,
            clean_price(text_of(card, "[class*='Listing-price']"), PRICE_EUR_RE), url, img))
    return out

def scrape_willhaben():
    out = []
    try:
        soup = fetch("https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz?keyword=subbuteo")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script: return out
        data = json.loads(script.string)
        ads = (data.get("props", {}).get("pageProps", {})
                   .get("searchResult", {}).get("advertSummaryList", {})
                   .get("advertSummary", []))
        for ad in ads:
            attrs = {a["name"]: a["values"][0]
                     for a in ad.get("attributes", {}).get("attribute", [])
                     if a.get("values")}
            title = attrs.get("HEADING", "")
            if not match_keyword(title): continue
            price = attrs.get("PRICE")
            img = attrs.get("MAIN_IMAGE_URL")
            url = f"https://www.willhaben.at/iad/kaufen-und-verkaufen/d/{ad.get('id','')}"
            out.append(make_listing("Willhaben.at", "Austria", "🇦🇹", title,
                f"€ {price}" if price else None, url, img))
    except Exception as e:
        logger.error(f"Willhaben: {e}")
    return out

SCRAPERS = [
    ("Marktplaats 🇳🇱",   scrape_marktplaats),
    ("Finn.no 🇳🇴",        scrape_finn),
    ("DBA.dk 🇩🇰",         scrape_dba),
    ("Kleinanzeigen 🇩🇪",  scrape_kleinanzeigen),
    ("OLX.pt 🇵🇹",         scrape_olx_pt),
    ("2dehands 🇧🇪",       scrape_2dehands),
    ("Willhaben 🇦🇹",      scrape_willhaben),
]

class SubbuteoScraper:
    def __init__(self, db):
        self.db = db

    def run_all(self) -> int:
        total_new = 0
        new_listings = []
        for name, fn in SCRAPERS:
            logger.info(f"Scraping {name}...")
            try:
                listings = fn()
                logger.info(f"  → {len(listings)} annunci trovati")
            except Exception as e:
                logger.error(f"Errore in {name}: {e}")
                listings = []
            for listing in listings:
                if self.db.insert(listing):
                    total_new += 1
                    new_listings.append(listing)
            time.sleep(random.uniform(2, 4))
        self.db.log_scan(total_new, len(SCRAPERS))
        logger.info(f"Scansione completata — {total_new} nuovi annunci")
        if new_listings:
            try:
                from notifier import send_telegram_batch
                send_telegram_batch(new_listings)
                for l in new_listings:
                    self.db.mark_notified(l["id"])
            except Exception as e:
                logger.error(f"Errore Telegram: {e}")
        return total_new
