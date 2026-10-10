import os
import sys

from dotenv import load_dotenv

from storage import connect, count_items, save_item
from urls import InvalidUrlError

if len(sys.argv) != 2:
    print('Usage: python src/save.py "https://example.com/post"')
    sys.exit(2)

load_dotenv()
conn = connect(os.environ.get("READLATER_DB", "data/readlater.db"))

try:
    item, created = save_item(conn, sys.argv[1])
except InvalidUrlError as e:
    print(f"SAVE FAILED: {e}")
    sys.exit(1)

print("NEW" if created else "ALREADY SAVED")
print("id:  ", item["id"])
print("url: ", item["normalized_url"])
print("rows:", count_items(conn))
