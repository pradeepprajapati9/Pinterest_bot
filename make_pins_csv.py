"""Build a Pinterest "Bulk create Pins" CSV from the fetched Amazon deals.

Why this exists: Pinterest denied API trial access for this app (the v5 API
returns 401 "application consumer type is not supported"), so pin_deal.py can't
publish. Pinterest's own bulk upload needs no API approval and no ban risk.

Flow:
  python fetch_deals.py      # pull fresh trending products (auto)
  python make_pins_csv.py    # writes pins.csv           (auto)
  -> upload pins.csv once at Pinterest > Create > Bulk create Pins   (10 seconds)

Each product is written once; already-exported ones are skipped on the next run.

Usage:
  python make_pins_csv.py             # up to 10 new pins -> pins.csv
  python make_pins_csv.py --limit 25  # bigger batch
  python make_pins_csv.py --dry       # show rows, write nothing
"""
import sys
import csv
import json
import re

import config
from bot import affiliate, caption

# Column order expected by Pinterest's bulk-create template.
COLUMNS = ["Title", "Media URL", "Pinterest board", "Thumbnail",
           "Description", "Link", "Publish date", "Keywords"]

DEFAULT_LIMIT = 10
CSV_FILE = config.BASE_DIR / "pins.csv"


def _arg(name: str, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def _keywords(description: str) -> str:
    """Pinterest wants comma-separated keywords; reuse the hashtags Gemini wrote."""
    tags = re.findall(r"#(\w+)", description)
    return ", ".join(tags[:5])


def main():
    dry = "--dry" in sys.argv
    limit = int(_arg("--limit", DEFAULT_LIMIT))

    board = config.PINTEREST_BOARD_NAME
    if not board:
        print("Set PINTEREST_BOARD_NAME in .env (the exact board name on Pinterest).")
        return

    data = json.loads(config.DEALS_FILE.read_text("utf-8"))
    deals = data.get("deals", [])
    todo = [d for d in deals if d.get("image") and not d.get("exported")][:limit]

    if not todo:
        print("No new products to export. Run fetch_deals.py first.")
        return

    rows = []
    for d in todo:
        title, desc = caption.make_pin_text(d["title"])
        rows.append({
            "Title": title,
            "Media URL": d["image"],
            "Pinterest board": board,
            "Thumbnail": "",
            "Description": desc,
            "Link": affiliate.affiliate_link(d["url"]),
            "Publish date": "",          # blank = publish on upload
            "Keywords": _keywords(desc),
        })
        print(f"  + {title}")

    if dry:
        print(f"\n(--dry) {len(rows)} row(s) ready, nothing written.")
        return

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    for d in todo:
        d["exported"] = True
    config.DEALS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    print(f"\nWrote {len(rows)} pin(s) -> {CSV_FILE}")
    print("Upload it at: Pinterest > Create > Bulk create Pins")


if __name__ == "__main__":
    main()
