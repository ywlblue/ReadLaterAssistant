import logging
import os

import requests
from dotenv import load_dotenv

from api import SaveResponse
from logging_config import setup_logging

load_dotenv()
approved_from_id = os.environ["ACCEPT_BOT_FROM_ID"]
token = os.environ["TELEGRAM_BOT_TOKEN"]
request_url = f"https://api.telegram.org/bot{token}"

setup_logging()
logger = logging.getLogger(__name__)


def get_updates(offset: int = None, timeout: int = 30):
    while True:
        response = requests.get(
            f"{request_url}/getUpdates",
            params={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": '["message"]'},
            timeout=40)
        response.raise_for_status()
        data = response.json()

        if not data["ok"]:
            raise RuntimeError(data["description"])

        for update in data["result"]:
            message = update.get("message", {})
            from_id = message.get("from", {}).get("id", "")
            text = message.get("text")

            if text:
                print(f"Received message：{text}")

            offset = update["update_id"] + 1
            chat_id = message.get("chat", {}).get("id", "")

            if str(from_id) != approved_from_id:
                unapproved_id_error = f"Received message from unapproved user id: {from_id}"
                logger.warning(unapproved_id_error)
                continue

            if chat_id:
                try:
                    response = requests.post(
                        "http://localhost:8000/save",
                        json={"url": text},
                        timeout=120,
                    )
                    save_response = SaveResponse.model_validate_json(response.text)
                    text = None
                    if save_response.status == "digested":
                        text = (f"Saved: {save_response.title}\n"
                                f"Summary: {save_response.digest.summary}\n"
                                f"Tags: {save_response.digest.tags}")
                    elif save_response.status == "digest_failed":
                        text = (f"Saved: {save_response.title}\n"
                                f"Error: {save_response.error}\n"
                                f"Send the same url again to retry.")
                    elif save_response.status == "fetch_failed":
                        text = f"Fetch failure: {save_response.error}"
                    else:
                        logger.warning(f"Unknown response status: {save_response.status}")
                    send_message(text, chat_id)
                except Exception as e:
                    logger.error(str(e))
                    send_message(f"Encounter an error: {str(e)}", chat_id)


def send_message(text: str, chat_id: str):
    print("Sending message")
    if text:
        response = requests.post(
            f"{request_url}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=30)
        response.raise_for_status()
        print(response.json())


if __name__ == '__main__':
    get_updates()
