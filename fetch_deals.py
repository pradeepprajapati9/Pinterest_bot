"""Fetch LIVE Amazon India deals and refresh deals.json (real price-drop products).

What it does:
  Amazon.in "Bestsellers" pages list the top-selling / trending products per
  category (static HTML, scraper-friendly). We scrape a few of those pages, pull
  the trending /dp/<ASIN> product links, grab each title, and merge the freshest
  ones into deals.json (as unposted). main.py then posts them one-by-one with
  YOUR affiliate tag + a Gemini caption.

Honest limits (free / no PA-API):
  Amazon blocks datacenter IPs with a captcha, so from GitHub Actions this may
  fetch nothing. That's fine -> we LEAVE the existing deals.json untouched so the
  bot still has deals to post. For best live results, run this locally (home wifi)
  on a schedule, or upgrade to the Amazon Product Advertising API after 3 sales.

Usage:
  python fetch_deals.py          # refresh deals.json from live pages
  python fetch_deals.py --dry    # show what it found, don't write
"""
import sys
import re
import html
import json
import time

import requests

import config

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "en-IN,en;q=0.9"}

# Bestsellers = top-selling / trending products per category (static, scrapable).
SOURCES = [
    "https://www.amazon.in/gp/bestsellers/electronics/",
    "https://www.amazon.in/gp/bestsellers/computers/",
    "https://www.amazon.in/gp/bestsellers/kitchen/",
    "https://www.amazon.in/gp/bestsellers/beauty/",
    "https://www.amazon.in/gp/bestsellers/shoes/",
    "https://www.amazon.in/gp/bestsellers/sports/",
]

# Each bestseller item: <div id="ASIN" ...> ... <img alt="Product Title" src="...jpg">
ITEM_RE = re.compile(r'id="([A-Z0-9]{10})"[\s\S]{0,800}?alt="([^"]+)"\s+src="([^"]+)"')
MAX_PER_SOURCE = 3     # top few trending items per category
MAX_NEW = 12           # cap fresh products added per run
MAX_DEALS = 40         # keep deals.json from growing forever


def _clean_title(raw: str) -> str:
    t = html.unescape(raw)                          # &amp; -> &, &#x27; -> '
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"(?i)\s*[:|-].*amazon.*$", "", t)   # drop 'Amazon.in' suffix
    t = re.sub(r"(?i)^amazon\.in[:\s]*", "", t)
    t = re.sub(r"(?i)^buy\s+", "", t)
    return t.strip()[:80]


def _big_image(url: str) -> str:
    """Listing thumbs are ~300px; Pinterest wants a large image. Ask for 1000px."""
    return re.sub(r"\._[A-Z0-9_,]+_\.jpg", "._AC_UL1000_.jpg", html.unescape(url))


def fetch_items(url: str) -> list:
    """Return [(asin, title, image), ...] parsed straight from one listing page."""
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200:
            print(f"  ! {url} -> HTTP {r.status_code}")
            return []
        if "captcha" in r.text.lower() or "api-services-support@amazon" in r.text:
            print(f"  ! {url} -> blocked (captcha)")
            return []
        seen, items = set(), []
        for asin, raw_title, raw_img in ITEM_RE.findall(r.text):
            if asin in seen:
                continue
            title = _clean_title(raw_title)
            bad = ("robot", "captcha", "sorry")
            if len(title) > 5 and not any(b in title.lower() for b in bad):
                seen.add(asin)
                items.append((asin, title, _big_image(raw_img)))
            if len(items) >= MAX_PER_SOURCE:
                break
        return items
    except Exception as ex:
        print(f"  ! {url} -> {ex}")
        return []


def collect_live_deals() -> list:
    """Return a list of {title, url, image, posted:False} for trending products."""
    seen = set()
    found = []
    for src in SOURCES:
        if len(found) >= MAX_NEW:
            break
        print(f"  scanning {src}")
        for asin, title, image in fetch_items(src):
            if asin in seen or len(found) >= MAX_NEW:
                continue
            seen.add(asin)
            found.append({
                "title": title,
                "url": f"https://www.amazon.in/dp/{asin}",
                "image": image,
                "posted": False,
                "pinned": False,
            })
            print(f"    + {title}")
        time.sleep(1)   # be polite / reduce block risk
    return found


def main():
    dry = "--dry" in sys.argv

    data = json.loads(config.DEALS_FILE.read_text("utf-8"))
    deals = data.get("deals", [])
    existing_urls = {d["url"] for d in deals}

    fresh = [d for d in collect_live_deals() if d["url"] not in existing_urls]

    if not fresh:
        print("\nNo fresh live deals fetched (likely blocked). "
              "Keeping existing deals.json unchanged.")
        return

    print(f"\nFetched {len(fresh)} new live deal(s).")

    if dry:
        print("(--dry) Not writing. Would add:")
        for d in fresh:
            print(f"   {d['title']}  ->  {d['url']}")
        return

    # Newest live deals first (posted next), then keep recent history, trim old.
    merged = fresh + deals
    if len(merged) > MAX_DEALS:
        merged = merged[:MAX_DEALS]
    data["deals"] = merged
    config.DEALS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    print(f"deals.json refreshed: {len(fresh)} new, {len(merged)} total.")


if __name__ == "__main__":
    main()
