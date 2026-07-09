"""Build a Pinterest "Bulk create Pins" CSV from the fetched Amazon deals.

Why this exists: Pinterest denied API trial access for this app (the v5 API
returns 401 "application consumer type is not supported"), so pin_deal.py can't
publish. Pinterest's own bulk upload needs no API approval and no ban risk.

Flow:
  python fetch_deals.py      # pull fresh trending products (auto, daily)
  python make_pins_csv.py    # APPENDS new pins to pins.csv (auto, daily)
  -> whenever you like (weekly is fine), upload pins.csv at
     Pinterest > Create > Bulk create Pins, then run --clear

Rows accumulate so you never have to upload daily. Each product is exported
once. Pinterest accepts up to 200 rows per upload, so we stop there.

Usage:
  python make_pins_csv.py             # add up to 10 new pins to pins.csv
  python make_pins_csv.py --limit 25  # bigger batch
  python make_pins_csv.py --dry       # show rows, write nothing
  python make_pins_csv.py --clear     # after uploading: empty pins.csv
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
MAX_ROWS = 200            # Pinterest's per-upload cap
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


def _existing_rows() -> list:
    if not CSV_FILE.exists():
        return []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    dry = "--dry" in sys.argv
    limit = int(_arg("--limit", DEFAULT_LIMIT))

    if "--clear" in sys.argv:
        CSV_FILE.unlink(missing_ok=True)
        print("pins.csv cleared. New pins will start collecting again.")
        return

    board = config.PINTEREST_BOARD_NAME
    if not board:
        print("Set PINTEREST_BOARD_NAME in .env (the exact board name on Pinterest).")
        return

    existing = _existing_rows()
    room = MAX_ROWS - len(existing)
    if room <= 0:
        print(f"pins.csv already holds {len(existing)} pins (Pinterest's cap). "
              f"Upload it, then run: python make_pins_csv.py --clear")
        return

    data = json.loads(config.DEALS_FILE.read_text("utf-8"))
    deals = data.get("deals", [])
    todo = [d for d in deals if d.get("image") and not d.get("exported")][:min(limit, room)]

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

    # Append, so pins pile up between uploads and you never have to do this daily.
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(existing + rows)

    for d in todo:
        d["exported"] = True
    config.DEALS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    total = len(existing) + len(rows)
    print(f"\nAdded {len(rows)} pin(s). pins.csv now holds {total}/{MAX_ROWS}.")
    print("Upload at Pinterest > Create > Bulk create Pins, then: python make_pins_csv.py --clear")


if __name__ == "__main__":
    main()
