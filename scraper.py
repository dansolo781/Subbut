"""
Subbuteo Scraper v2 — API mobile dei siti di annunci
Niente scraping HTML, niente browser. Solo API JSON dirette.
"""
import hashlib
import logging
import time
import random
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

KEYWORDS = ["subbuteo", "subbut", "subboteo", "subbutéo", "subbueto"]

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def keyword_match(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in KEYWORDS)

def get_json(url: str, headers: dict = None, params: dict = None, timeout: int = 15) -> Optional[dict]:
    h = {**HEADERS_MOBILE, **(headers or {})}
    try:
        resp = httpx.get(url, headers=h, params=params, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"GET {url} → {e}")
        return None

# ---------------------------------------------------------------------------
# SPAGNA — Wallapop API
# ---------------------------------------------------------------------------
def scrape_wallapop():
    results = []
    url = "https://api.wallapop.com/api/v3/general/search"
    params = {
        "keywords": "subbuteo",
        "filters_source": "search_box",
        "order_by": "newest",
        "start": 0,
        "step": 40,
    }
    data = get_json(url, params=params)
    if not data:
        return results
    items = data.get("data", {}).get("section", {}).get("payload", {}).get("items", [])
    for item in items:
        cnt = item.get("content", {})
        title = cnt.get("title", "")
        if not keyword_match(title):
            continue
        price_val = cnt.get("price", {})
        price = f"{price_val.get('amount','')} {price_val.get('currency','')}".strip() if isinstance(price_val, dict) else str(price_val)
        slug = cnt.get("web_slug", cnt.get("id", ""))
        href = f"https://es.wallapop.com/item/{slug}"
        imgs = cnt.get("images", [])
        img = imgs[0].get("medium") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "Wallapop", "country": "Spagna", "country_flag": "🇪🇸", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# GERMANIA — Kleinanzeigen API
# ---------------------------------------------------------------------------
def scrape_kleinanzeigen():
    results = []
    url = "https://www.kleinanzeigen.de/s-subbuteo/k0.json"
    data = get_json(url, headers={"Accept": "application/json"})
    if not data:
        # fallback: prova endpoint alternativo
        url2 = "https://www.kleinanzeigen.de/s-suchergebnisse.json?keywords=subbuteo&sortingField=CREATION_DATE&sortingOrder=DESCENDING"
        data = get_json(url2)
    if not data:
        return results
    ads = data.get("ads", {}).get("ad", []) or data.get("searchResults", {}).get("adList", []) or []
    if isinstance(ads, dict):
        ads = [ads]
    for ad in ads:
        title = ad.get("title", "") or ad.get("headline", "")
        if not keyword_match(title):
            continue
        ad_id = ad.get("id", "") or ad.get("adId", "")
        href = f"https://www.kleinanzeigen.de/s-anzeige/{ad_id}"
        price_obj = ad.get("price", {}) or {}
        price = price_obj.get("amount", "") or ad.get("priceLabel", "")
        img = None
        pictures = ad.get("pictures", {}).get("picture", []) or []
        if isinstance(pictures, dict):
            pictures = [pictures]
        if pictures:
            img = pictures[0].get("link", [{}])[0].get("href") if isinstance(pictures[0].get("link"), list) else None
        results.append({"id": make_id(href), "title": title, "price": str(price) if price else None, "url": href, "image_url": img, "site": "Kleinanzeigen.de", "country": "Germania", "country_flag": "🇩🇪", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# OLANDA — Marktplaats API
# ---------------------------------------------------------------------------
def scrape_marktplaats():
    results = []
    url = "https://www.marktplaats.nl/lrp/api/search"
    params = {"query": "subbuteo", "sortBy": "SORT_INDEX", "sortOrder": "DECREASING", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    listings = data.get("listings", [])
    for item in listings:
        title = item.get("title", "")
        if not keyword_match(title):
            continue
        item_id = item.get("itemId", "")
        href = f"https://www.marktplaats.nl/v/overige/{item_id}"
        price_info = item.get("priceInfo", {})
        price = price_info.get("priceCents")
        price_str = f"€{price/100:.2f}" if price else price_info.get("priceType")
        imgs = item.get("pictures", [])
        img = imgs[0].get("mediumUrl") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Marktplaats.nl", "country": "Olanda", "country_flag": "🇳🇱", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# NORVEGIA — Finn.no API
# ---------------------------------------------------------------------------
def scrape_finn():
    results = []
    url = "https://www.finn.no/api/search-qf"
    params = {"searchkey": "SEARCH_ID_BAP_ALL", "q": "subbuteo", "sort": "PUBLISHED_DESC", "rows": 30}
    data = get_json(url, headers={"Accept": "application/json"}, params=params)
    if not data:
        return results
    docs = data.get("docs", [])
    for doc in docs:
        title = doc.get("heading", "")
        if not keyword_match(title):
            continue
        ad_id = doc.get("ad_id", "")
        href = f"https://www.finn.no/bap/forsale/ad.html?finnkode={ad_id}"
        price_obj = doc.get("price", {})
        price = f"{price_obj.get('amount', '')} {price_obj.get('currency_code', '')}".strip() if isinstance(price_obj, dict) else None
        img = doc.get("image", {}).get("url") if isinstance(doc.get("image"), dict) else None
        results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "Finn.no", "country": "Norvegia", "country_flag": "🇳🇴", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# SVEZIA — Blocket API
# ---------------------------------------------------------------------------
def scrape_blocket():
    results = []
    url = "https://api.blocket.se/search_bff/v1/content"
    params = {"q": "subbuteo", "st": "s", "cg": "0", "w": "3", "c": "0", "gl": "3", "include": "all", "rows": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    items = data.get("data", [])
    for item in items:
        title = item.get("subject", "")
        if not keyword_match(title):
            continue
        href = item.get("share_url") or f"https://www.blocket.se/annons/{item.get('ad_id','')}"
        price_obj = item.get("price", {})
        price = f"{price_obj.get('value','')} {price_obj.get('suffix','')}".strip() if isinstance(price_obj, dict) else None
        imgs = item.get("images", [])
        img = imgs[0].get("url") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "Blocket.se", "country": "Svezia", "country_flag": "🇸🇪", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# FINLANDIA — Tori.fi API
# ---------------------------------------------------------------------------
def scrape_tori():
    results = []
    url = "https://api.tori.fi/api/v1.2/listings"
    params = {"q": "subbuteo", "sort": "dtime_desc", "limit": 30, "ca": "0"}
    data = get_json(url, params=params)
    if not data:
        return results
    listings = data.get("listings", [])
    for item in listings:
        title = item.get("subject", "")
        if not keyword_match(title):
            continue
        href = item.get("list_id_code", "")
        if href:
            href = f"https://www.tori.fi/{href}.htm"
        else:
            href = item.get("url", "")
        price = item.get("price", {}).get("value") if isinstance(item.get("price"), dict) else item.get("price")
        price_str = f"{price} €" if price else None
        img = item.get("image", {}).get("url") if isinstance(item.get("image"), dict) else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Tori.fi", "country": "Finlandia", "country_flag": "🇫🇮", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# DANIMARCA — DBA.dk API
# ---------------------------------------------------------------------------
def scrape_dba():
    results = []
    url = "https://api.dba.dk/v1/listings"
    params = {"q": "subbuteo", "sort": "creationDate,desc", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    items = data.get("listings", [])
    for item in items:
        title = item.get("heading", "")
        if not keyword_match(title):
            continue
        href = item.get("urls", {}).get("frontend", "") or f"https://www.dba.dk/{item.get('id','')}"
        price = item.get("price", {}).get("price") if isinstance(item.get("price"), dict) else item.get("price")
        price_str = f"{price} kr" if price else None
        imgs = item.get("images", [])
        img = imgs[0].get("url") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "DBA.dk", "country": "Danimarca", "country_flag": "🇩🇰", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# PORTOGALLO — OLX.pt + CustoJusto.pt
# ---------------------------------------------------------------------------
def scrape_olx_pt():
    results = []
    url = "https://www.olx.pt/api/v1/offers/"
    params = {"query": "subbuteo", "sort_by": "created_at:desc", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("data", []):
        title = item.get("title", "")
        if not keyword_match(title):
            continue
        href = item.get("url", "")
        params_price = item.get("params", [])
        price = None
        for p in params_price:
            if p.get("key") == "price":
                price = p.get("value", {}).get("label")
                break
        imgs = item.get("photos", [])
        img = imgs[0].get("link", "").replace("{width}", "400").replace("{height}", "300") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "OLX.pt", "country": "Portogallo", "country_flag": "🇵🇹", "found_at": datetime.now().isoformat()})
    return results

def scrape_custojusto():
    results = []
    url = "https://www.custojusto.pt/api/ads"
    params = {"q": "subbuteo", "o": 1, "st": "s"}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("data", {}).get("adList", []):
        title = item.get("subject", "")
        if not keyword_match(title):
            continue
        href = item.get("url", "") or f"https://www.custojusto.pt/{item.get('listId','')}"
        price = item.get("price", {}).get("value") if isinstance(item.get("price"), dict) else None
        price_str = f"{price} €" if price else None
        img = item.get("images", [None])[0]
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "CustoJusto.pt", "country": "Portogallo", "country_flag": "🇵🇹", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# SPAGNA — Milanuncios API
# ---------------------------------------------------------------------------
def scrape_milanuncios():
    results = []
    url = "https://www.milanuncios.com/api/v1/listings"
    params = {"q": "subbuteo", "ord": "date", "fromSearch": 1}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("adList", []):
        title = item.get("description", "")
        if not keyword_match(title):
            continue
        href = f"https://www.milanuncios.com{item.get('url','')}"
        price = item.get("price")
        price_str = f"{price} €" if price else None
        img = item.get("image")
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Milanuncios", "country": "Spagna", "country_flag": "🇪🇸", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# FRANCIA — Leboncoin API mobile
# ---------------------------------------------------------------------------
def scrape_leboncoin():
    results = []
    url = "https://api.leboncoin.fr/api/adfinder/v1/search"
    payload = {
        "filters": {
            "category": {"id": "0"},
            "keywords": {"text": "subbuteo"},
        },
        "sort_by": "time",
        "sort_order": "desc",
        "limit": 30,
        "offset": 0,
    }
    try:
        resp = httpx.post(url, json=payload, headers={
            **HEADERS_MOBILE,
            "api_key": "ba0c2dad52b3565fd92a93e9a1d5cb88",
            "Content-Type": "application/json",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Leboncoin API: {e}")
        return results
    for item in data.get("ads", []):
        title = item.get("subject", "")
        if not keyword_match(title):
            continue
        href = item.get("url", "") or f"https://www.leboncoin.fr/annonces/{item.get('list_id','')}"
        price = item.get("price", [None])[0] if item.get("price") else None
        price_str = f"{price} €" if price else None
        imgs = item.get("images", {}).get("urls_large") or item.get("images", {}).get("urls", [])
        img = imgs[0] if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Leboncoin.fr", "country": "Francia", "country_flag": "🇫🇷", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# SVIZZERA — Anibis + Tutti.ch
# ---------------------------------------------------------------------------
def scrape_anibis():
    results = []
    url = "https://www.anibis.ch/api/v3/listings/search"
    params = {"q": "subbuteo", "sort": "Date", "lang": "fr", "pi": 1, "ps": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("listings", []):
        title = item.get("title", "")
        if not keyword_match(title):
            continue
        href = item.get("listingUrl", "") or f"https://www.anibis.ch/fr/{item.get('id','')}"
        price = item.get("price", {}).get("amount") if isinstance(item.get("price"), dict) else None
        price_str = f"CHF {price}" if price else None
        imgs = item.get("images", [])
        img = imgs[0].get("url") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Anibis.ch", "country": "Svizzera", "country_flag": "🇨🇭", "found_at": datetime.now().isoformat()})
    return results

def scrape_tutti():
    results = []
    url = "https://www.tutti.ch/api/v10/listings"
    params = {"q": "subbuteo", "sort": "date_desc", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("listings", []):
        title = item.get("subject", "")
        if not keyword_match(title):
            continue
        href = item.get("urls", {}).get("canonical", "") or f"https://www.tutti.ch/{item.get('id','')}"
        price = item.get("price", {}).get("amount") if isinstance(item.get("price"), dict) else None
        price_str = f"CHF {price}" if price else None
        imgs = item.get("images", [])
        img = imgs[0].get("url") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Tutti.ch", "country": "Svizzera", "country_flag": "🇨🇭", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# AUSTRIA — Willhaben API
# ---------------------------------------------------------------------------
def scrape_willhaben():
    results = []
    url = "https://api.willhaben.at/iad/v1.2/attribute-groups/auto/facets/1/job-listings"
    url = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz"
    params = {"keyword": "subbuteo", "sort": "1", "rows": 30, "isNavigation": "true"}
    data = get_json(url, params=params)
    if not data:
        return results
    items = data.get("advertSummaryList", {}).get("advertSummary", [])
    for item in items:
        attrs = {a.get("name"): a.get("values", [None])[0] for a in item.get("attributes", {}).get("attribute", [])}
        title = attrs.get("HEADING", "")
        if not keyword_match(title):
            continue
        ad_id = item.get("id", "")
        href = f"https://www.willhaben.at/iad/kaufen-und-verkaufen/d/{ad_id}"
        price = attrs.get("PRICE")
        price_str = f"{price} €" if price else None
        img = attrs.get("MAIN_IMAGE_URL")
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Willhaben.at", "country": "Austria", "country_flag": "🇦🇹", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# BELGIO — 2dehands/2ememain API
# ---------------------------------------------------------------------------
def scrape_2dehands():
    results = []
    for domain, country_site, flag in [
        ("www.2dehands.be", "2dehands.be", "🇧🇪"),
        ("www.2ememain.be", "2ememain.be", "🇧🇪"),
    ]:
        url = f"https://{domain}/lrp/api/search"
        params = {"query": "subbuteo", "sortBy": "SORT_INDEX", "sortOrder": "DECREASING", "limit": 30}
        data = get_json(url, params=params)
        if not data:
            continue
        for item in data.get("listings", []):
            title = item.get("title", "")
            if not keyword_match(title):
                continue
            item_id = item.get("itemId", "")
            href = f"https://{domain}/v/overige/{item_id}"
            price_info = item.get("priceInfo", {})
            price = price_info.get("priceCents")
            price_str = f"€{price/100:.2f}" if price else price_info.get("priceType")
            imgs = item.get("pictures", [])
            img = imgs[0].get("mediumUrl") if imgs else None
            results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": country_site, "country": "Belgio", "country_flag": flag, "found_at": datetime.now().isoformat()})
        time.sleep(1)
    return results

# ---------------------------------------------------------------------------
# BRASILE — OLX Brasil API
# ---------------------------------------------------------------------------
def scrape_olx_br():
    results = []
    url = "https://www.olx.com.br/api/v1/offers/"
    params = {"query": "subbuteo", "sort_by": "created_at:desc", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        return results
    for item in data.get("data", []):
        title = item.get("title", "")
        if not keyword_match(title):
            continue
        href = item.get("url", "")
        params_list = item.get("params", [])
        price = None
        for p in params_list:
            if p.get("key") == "price":
                price = p.get("value", {}).get("label")
                break
        imgs = item.get("photos", [])
        img = imgs[0].get("link", "").replace("{width}", "400").replace("{height}", "300") if imgs else None
        results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "OLX.br", "country": "Brasile", "country_flag": "🇧🇷", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# MALTA — maltapark.com
# ---------------------------------------------------------------------------
def scrape_maltapark():
    results = []
    url = "https://www.maltapark.com/api/search"
    params = {"q": "subbuteo", "sort": "recent", "limit": 30}
    data = get_json(url, params=params)
    if not data:
        # fallback HTML leggero
        try:
            resp = httpx.get("https://www.maltapark.com/search/?q=subbuteo", headers=HEADERS_MOBILE, timeout=15)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select(".item, article, [class*='listing']"):
                a = card.select_one("a[href]")
                if not a:
                    continue
                href = a.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.maltapark.com" + href
                title = card.select_one("h2,h3,[class*='title']")
                title = title.get_text(strip=True) if title else a.get_text(strip=True)
                if not keyword_match(title + href):
                    continue
                price_el = card.select_one("[class*='price']")
                price = price_el.get_text(strip=True) if price_el else None
                img_el = card.select_one("img")
                img = img_el.get("src") if img_el else None
                results.append({"id": make_id(href), "title": title, "price": price, "url": href, "image_url": img, "site": "Maltapark.com", "country": "Malta", "country_flag": "🇲🇹", "found_at": datetime.now().isoformat()})
        except Exception as e:
            logger.warning(f"Maltapark fallback: {e}")
        return results
    for item in data.get("items", []):
        title = item.get("title", "")
        if not keyword_match(title):
            continue
        href = f"https://www.maltapark.com/item/{item.get('id','')}"
        price = item.get("price")
        price_str = f"€{price}" if price else None
        img = item.get("image")
        results.append({"id": make_id(href), "title": title, "price": price_str, "url": href, "image_url": img, "site": "Maltapark.com", "country": "Malta", "country_flag": "🇲🇹", "found_at": datetime.now().isoformat()})
    return results

# ---------------------------------------------------------------------------
# Runner principale
# ---------------------------------------------------------------------------

SCRAPERS = [
    ("Wallapop 🇪🇸",          scrape_wallapop),
    ("Milanuncios 🇪🇸",       scrape_milanuncios),
    ("Kleinanzeigen 🇩🇪",     scrape_kleinanzeigen),
    ("Marktplaats 🇳🇱",       scrape_marktplaats),
    ("2dehands/2ememain 🇧🇪", scrape_2dehands),
    ("Finn.no 🇳🇴",           scrape_finn),
    ("Blocket.se 🇸🇪",        scrape_blocket),
    ("Tori.fi 🇫🇮",           scrape_tori),
    ("DBA.dk 🇩🇰",            scrape_dba),
    ("OLX.pt 🇵🇹",            scrape_olx_pt),
    ("CustoJusto.pt 🇵🇹",     scrape_custojusto),
    ("Leboncoin.fr 🇫🇷",      scrape_leboncoin),
    ("Anibis.ch 🇨🇭",         scrape_anibis),
    ("Tutti.ch 🇨🇭",          scrape_tutti),
    ("Willhaben.at 🇦🇹",      scrape_willhaben),
    ("OLX.br 🇧🇷",            scrape_olx_br),
    ("Maltapark 🇲🇹",         scrape_maltapark),
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
            time.sleep(random.uniform(1, 3))
        self.db.log_scan(total_new, len(SCRAPERS))
        logger.info(f"Scansione completata — {total_new} nuovi annunci")
        if new_listings:
            try:
                from notifier import send_telegram_batch
                send_telegram_batch(new_listings)
                for l in new_listings:
                    self.db.mark_notified(l["id"])
            except Exception as e:
                logger.error(f"Errore notifica Telegram: {e}")
        return total_new
