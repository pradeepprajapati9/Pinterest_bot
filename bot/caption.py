"""Write deal copy with Gemini (free), with safe fallbacks.

make_caption()  -> chatty Hindi+English caption for the Telegram channel
make_pin_text() -> keyword-rich title + description for Pinterest (a search engine)
"""
import time
import requests
import config

MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]


def _gemini(prompt: str) -> str:
    if not config.GEMINI_API_KEY:
        return ""
    for attempt in range(2):
        for model in MODELS:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{model}:generateContent?key={config.GEMINI_API_KEY}")
            try:
                r = requests.post(url, timeout=40,
                                  json={"contents": [{"parts": [{"text": prompt}]}]})
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if r.status_code in (429, 503):
                    continue
            except Exception as ex:
                print(f"[caption] {model} error: {ex}")
        if attempt == 0:
            time.sleep(3)
    return ""


def make_caption(title: str) -> str:
    prompt = (
        f"Write a short, exciting Telegram deal-channel caption (Hindi + English mix) "
        f"for this product: '{title}'. 2-3 lines, 1-2 emojis, create genuine urgency "
        f"(limited-time / best price) WITHOUT inventing a specific price or fake discount. "
        f"End with a line like 'Abhi grab karo 👇'. Plain text only, no markdown."
    )
    text = _gemini(prompt)
    if not text:
        text = f"🔥 {title} — aaj ka best deal!\nLimited time offer. Abhi grab karo 👇"
    return text


def make_pin_text(title: str) -> tuple:
    """Return (pin_title, description) tuned for Pinterest search, not for hype.

    People find pins by searching ('best wireless earbuds under 2000'), so the copy
    must read like a real search phrase, in English. Pinterest caps title at 100
    chars and description at 500.
    """
    prompt = (
        f"For this product: '{title}'\n"
        f"Write Pinterest pin copy in English that ranks in Pinterest search.\n"
        f"Line 1: a searchable pin title, max 90 characters, no emojis, no price.\n"
        f"Line 2: a 2-3 sentence description (max 350 chars) using natural shopping "
        f"keywords buyers type, ending with 3-5 relevant hashtags.\n"
        f"Do NOT invent a price or discount percentage. Output exactly 2 lines, "
        f"plain text, no labels, no markdown."
    )
    text = _gemini(prompt)
    lines = [l.strip() for l in text.splitlines() if l.strip()] if text else []
    if len(lines) >= 2:
        return lines[0][:100], lines[1][:500]
    short = title[:90]
    return short, (f"{title}. Check the latest price and offers on Amazon India. "
                   f"#amazonfinds #dealsindia #onlineshopping")
