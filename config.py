"""Config for the deal/affiliate bot (Telegram + Pinterest). Reads .env with safe defaults."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

BASE_DIR = Path(__file__).parent
DEALS_FILE = BASE_DIR / "deals.json"   # product list + posted flags
LOG_FILE = BASE_DIR / "bot.log"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "").strip()
AMAZON_ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DO_POST = os.getenv("DO_POST", "false").lower() == "true"

# Pinterest: board to pin into + API v5 access token (scopes: pins:write, boards:read)
PINTEREST_TOKEN = os.getenv("PINTEREST_TOKEN", "").strip()
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID", "").strip()
