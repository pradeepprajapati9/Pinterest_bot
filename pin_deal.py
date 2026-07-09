"""Pinterest deal bot - creates one Pin per run.

  pick next un-pinned product -> build YOUR affiliate link -> Gemini pin copy
  -> create the Pin on your board -> mark pinned

Why Pinterest: people search it in shopping mood, so the platform brings the
buyers to you - you never have to recruit followers. A pin also keeps surfacing
in search for months, unlike a Telegram post that scrolls away in an hour.

Only real products (with an image) can be pinned; the old category links in
deals.json are skipped automatically.

Run on a schedule (GitHub Actions). With DO_POST=false it just prints the pin.
"""
import sys
import json
import traceback
from datetime import datetime

import config
from bot import affiliate, caption, pinterest

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def log(msg: str):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load():
    return json.loads(config.DEALS_FILE.read_text("utf-8"))


def _save(data):
    config.DEALS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def run():
    data = _load()
    deals = data.get("deals", [])
    pinnable = [d for d in deals if d.get("image")]
    if not pinnable:
        log("No pinnable products yet. Run fetch_deals.py first.")
        return

    nxt = next((d for d in pinnable if not d.get("pinned")), None)
    if not nxt:
        # every product pinned once. Don't re-pin the same image+link: Pinterest
        # treats that as spam. Wait for fetch_deals.py to bring fresh products.
        log("All products already pinned. Waiting for fresh deals.")
        return

    link = affiliate.affiliate_link(nxt["url"])
    title, desc = caption.make_pin_text(nxt["title"])

    log(f"Pinning: {nxt['title']}")
    if pinterest.post(title, desc, link, nxt["image"]):
        nxt["pinned"] = True
        _save(data)
        log("Done.")
    else:
        log("Pin failed (will retry this product next run).")
        # exit non-zero so a scheduled run shows as FAILED instead of a
        # misleading green "success" when nothing was pinned.
        raise SystemExit("pin failed")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        log("ERROR:\n" + traceback.format_exc())
        sys.exit(1)
