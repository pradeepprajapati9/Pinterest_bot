"""Print your Pinterest boards + their IDs, so you can fill PINTEREST_BOARD_ID.

Setup first:
  1. Make your Pinterest account a *business* account (free, in settings).
  2. Create a board, e.g. "Amazon India Deals".
  3. https://developers.pinterest.com/apps/ -> create an app -> generate an
     access token with scopes: pins:write, boards:read
  4. Put that token in .env as PINTEREST_TOKEN, then run:  python get_board_id.py
"""
import requests
import config


def main():
    if not config.PINTEREST_TOKEN:
        print("Set PINTEREST_TOKEN in .env first (see this file's docstring).")
        return
    r = requests.get("https://api.pinterest.com/v5/boards", timeout=30,
                     headers={"Authorization": f"Bearer {config.PINTEREST_TOKEN}"})
    if r.status_code != 200:
        print(f"Failed: {r.status_code} {r.text[:300]}")
        return
    boards = r.json().get("items", [])
    if not boards:
        print("No boards found. Create a board on Pinterest first.")
        return
    print("Your boards:\n")
    for b in boards:
        print(f"  {b['id']}   {b['name']}")
    print("\nCopy the id you want into .env as PINTEREST_BOARD_ID")


if __name__ == "__main__":
    main()
