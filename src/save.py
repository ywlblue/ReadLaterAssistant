import os
import sys

from dotenv import load_dotenv

from fetch import fetch_url
from storage import count_items, record_fetch, save_item, connect, save_snapshot
from urls import InvalidUrlError

if len(sys.argv) != 2:
    print('Usage: python src/save.py "https://example.com/post"')
    sys.exit(2)

load_dotenv()
conn = connect(os.environ.get("READLATER_DB", "data/readlater.db"))

try:
    # Create item with url if not exist
    item, created = save_item(conn, sys.argv[1])
except InvalidUrlError as e:
    print(f"SAVE FAILED: {e}")
    sys.exit(1)

# Fetch article from saved item using normalized url
if item["status"] != "fetched":
    fetch_result = fetch_url(item["url"])
    snapshot_path = save_snapshot(item["id"], fetch_result.raw_html) if fetch_result.ok else None
    item = record_fetch(conn, item["id"], fetch_result, snapshot_path)

print("NEW" if created else "ALREADY SAVED")
print("id:    ", item["id"])
print("url:   ", item["normalized_url"])
print("status:", item["status"])
print("title: ", item["title"])
print("chars: ", len(item["content_text"] or ""))
print("error: ", item["error"])
print("rows:  ", count_items(conn))
