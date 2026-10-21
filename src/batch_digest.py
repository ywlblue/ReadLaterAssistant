import json
import logging
from pathlib import Path

import requests

from api import SaveResponse
from logging_config import setup_logging

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DATA_PATH = BASE_DIR / "data/links"
OUTPUT_DATA_PATH = BASE_DIR / "data/digested_link_result.jsonl"

setup_logging()
logger = logging.getLogger(__name__)

path = OUTPUT_DATA_PATH
results = []

if path.exists():
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

done = {
    item["input_url"]
    for item in results
}


def run():
    result = {"attempted": 0, "fetched": 0, "failed": 0, "digested": 0, "unknown": 0}
    with (
        open(INPUT_DATA_PATH, "r", encoding="utf-8") as infile,
        open(OUTPUT_DATA_PATH, "a", encoding="utf-8") as outfile
    ):
        for link in infile:
            link = link.strip()
            if not link:
                continue
            if link in done:
                logger.warning(f"Link {link} already processed. Skipped.")
                continue
            result["attempted"] += 1
            try:
                http_status, digest = get_digest(link)
                if http_status != 200:
                    data = {"input_url": link, "http_status": http_status,
                            "item_id": None, "status": "http_error", "error": digest}
                    result["failed"] += 1
                else:
                    data = {"input_url": link, "http_status": http_status,
                            "item_id": digest.item_id, "status": digest.status, "error": digest.error}
                    if digest.status == "digested":
                        print(f"Link: {link}. Status: Digested")
                        result["digested"] += 1
                        result["fetched"] += 1
                    elif digest.status == "fetched" or digest.status == "digest_failed":
                        print(f"Link: {link}. Status: Fetched")
                        result["fetched"] += 1
                    elif digest.status == "fetch_failed":
                        print(f"Link: {link}. Status: Failed")
                        result["failed"] += 1
                    else:
                        print(f"Link: {link}. Status: Unknown")
                        result["unknown"] += 1
            except requests.exceptions.ConnectionError:
                logger.log(logging.ERROR, "Connection error. Check server status.")
                break
            except Exception as err:
                logger.log(logging.ERROR, f"Something wrong during processing: {link}. Error: {str(err)}")
                result["failed"] += 1
                data = {"input_url": link, "http_status": None,
                        "item_id": None, "status": "server_error", "error": str(err)}
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            outfile.flush()
    print(result)


def get_digest(link):
    response = requests.post("http://localhost:8000/save",
                             json={"url": link, "origin_type": "IMPORT"}, timeout=120)
    if response.status_code != 200:
        return response.status_code, response.json()["detail"]
    save_response = SaveResponse.model_validate(response.json())
    return response.status_code, save_response


if __name__ == '__main__':
    run()
