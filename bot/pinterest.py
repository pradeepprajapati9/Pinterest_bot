"""Create a Pin on your Pinterest board via the official API v5.

A pin = image + title + description + destination link (your affiliate link).
Pinterest fetches the image itself from `image_url`, so nothing is uploaded.

Needs a Pinterest *business* account, an app, and a token with `pins:write`.
With DO_POST=false this prints the pin instead of creating it (safe dry-run).
"""
import requests
import config

API = "https://api.pinterest.com/v5/pins"


def post(title: str, description: str, link: str, image_url: str) -> bool:
    if not config.DO_POST:
        print("=== DRY-RUN (DO_POST=false) — would pin: ===")
        print(f"  title : {title}")
        print(f"  desc  : {description}")
        print(f"  link  : {link}")
        print(f"  image : {image_url}\n")
        return True

    if not (config.PINTEREST_TOKEN and config.PINTEREST_BOARD_ID):
        print("[pinterest] missing PINTEREST_TOKEN / PINTEREST_BOARD_ID")
        return False
    if not image_url:
        print("[pinterest] deal has no image — skipping (a pin needs an image)")
        return False

    payload = {
        "board_id": config.PINTEREST_BOARD_ID,
        "title": title[:100],
        "description": description[:500],
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url,
        },
    }
    try:
        r = requests.post(API, timeout=45, json=payload, headers={
            "Authorization": f"Bearer {config.PINTEREST_TOKEN}",
            "Content-Type": "application/json",
        })
        if r.status_code in (200, 201):
            print(f"[pinterest] pinned ✓  (id {r.json().get('id', '?')})")
            return True
        print(f"[pinterest] failed: {r.status_code} {r.text[:300]}")
    except Exception as ex:
        print(f"[pinterest] error: {ex}")
    return False
