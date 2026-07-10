"""Build a public deals page (deals.html) from the products in deals.json.

Why: the pins have to point somewhere real. A live page that shows the same
curated deals is also what Pinterest's app reviewers look for - the website you
declare should obviously match the content you pin.

Writes to the tariffwise site by default (it is already on GitHub Pages), so the
page goes live at https://pradeepprajapati9.github.io/tariffwise/deals.html

Usage:
  python make_deals_page.py            # write the page
  python make_deals_page.py --dry      # print what it would contain
"""
import sys
import html
import json
from datetime import datetime

import config
from bot import affiliate

OUT = config.BASE_DIR.parent / "tariffwise" / "deals.html"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Today's Amazon India Deals — Dhamaka Deals</title>
  <meta name="description" content="A hand-picked list of trending Amazon India products, refreshed daily. Prices and availability are shown on Amazon." />
  <link rel="canonical" href="https://pradeepprajapati9.github.io/tariffwise/deals.html" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🛒</text></svg>" />
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
           color: #1f2328; background: #fff; line-height: 1.6; }}
    .wrap {{ max-width: 1040px; margin: 0 auto; padding: 32px 20px 64px; }}
    h1 {{ margin: 0 0 .2em; font-size: 2rem; }}
    .sub {{ color: #57606a; margin: 0 0 8px; }}
    .disclosure {{ background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 8px;
                  padding: 12px 14px; font-size: .9rem; color: #57606a; margin: 20px 0 28px; }}
    .grid {{ display: grid; gap: 20px;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }}
    .card {{ border: 1px solid #d0d7de; border-radius: 10px; overflow: hidden;
            display: flex; flex-direction: column; }}
    .card img {{ width: 100%; height: 200px; object-fit: contain; background: #fff; padding: 12px; }}
    .card .body {{ padding: 12px 14px 16px; display: flex; flex-direction: column; gap: 10px; flex: 1; }}
    .card h2 {{ font-size: .95rem; font-weight: 600; margin: 0; line-height: 1.4; }}
    .btn {{ margin-top: auto; display: block; text-align: center; text-decoration: none;
           background: #ff9900; color: #111; font-weight: 600; padding: 9px 12px;
           border-radius: 6px; font-size: .9rem; }}
    .btn:hover {{ background: #e88b00; }}
    footer {{ margin-top: 48px; font-size: .85rem; color: #57606a; }}
    footer a {{ color: #57606a; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #0d1117; color: #e6edf3; }}
      .card, .disclosure {{ border-color: #30363d; }}
      .disclosure {{ background: #161b22; color: #8b949e; }}
      .card img {{ background: #fff; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Today's Amazon India Deals</h1>
    <p class="sub">Hand-picked trending products, refreshed daily. Last updated: {updated}</p>

    <p class="disclosure">
      As an Amazon Associate I earn from qualifying purchases. Links below are
      affiliate links — they cost you nothing extra. Prices and availability are
      shown on Amazon and can change at any time.
    </p>

    <div class="grid">
{cards}
    </div>

    <footer>
      <p><a href="./privacy.html">Privacy Policy</a> &middot; <a href="./">Import duty calculator</a></p>
    </footer>
  </main>
</body>
</html>
"""

CARD = """      <article class="card">
        <img src="{image}" alt="{title}" loading="lazy" />
        <div class="body">
          <h2>{title}</h2>
          <a class="btn" href="{link}" target="_blank" rel="noopener nofollow sponsored">View on Amazon</a>
        </div>
      </article>"""


def main():
    dry = "--dry" in sys.argv

    data = json.loads(config.DEALS_FILE.read_text("utf-8"))
    products = [d for d in data.get("deals", []) if d.get("image")]
    if not products:
        print("No products with images yet. Run fetch_deals.py first.")
        return

    cards = "\n".join(
        CARD.format(image=html.escape(p["image"]),
                    title=html.escape(p["title"]),
                    link=html.escape(affiliate.affiliate_link(p["url"])))
        for p in products
    )
    page = PAGE.format(updated=f"{datetime.now():%d %B %Y}", cards=cards)

    if dry:
        print(f"(--dry) would write {len(products)} product(s) to {OUT}")
        return

    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {len(products)} product(s) -> {OUT}")
    print("Commit & push the tariffwise repo to publish it.")


if __name__ == "__main__":
    main()
