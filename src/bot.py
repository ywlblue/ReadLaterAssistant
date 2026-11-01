import logging
import os

import requests
from dotenv import load_dotenv

from api import SaveResponse, AskResponse
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
                print(f"Received message, len={len(text)}")

            offset = update["update_id"] + 1
            chat_id = message.get("chat", {}).get("id", "")

            if str(from_id) != approved_from_id:
                unapproved_id_error = f"Received message from unapproved user id: {from_id}"
                logger.warning(unapproved_id_error)
                continue

            if chat_id and text:
                command, _, arg = text.partition(" ")  # "/ask Can Vault..." → "/ask", "Can Vault..."
                handler = COMMANDS.get(command)
                try:
                    reply = handler(arg) if handler else handle_save(text)
                except Exception as e:
                    logger.error(str(e))
                    reply = f"Encounter an error: {e}"
                send_message(reply, chat_id)


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


def handle_save(text: str):
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
    return text


def handle_ask(query: str):
    response = requests.post(
        "http://localhost:8000/ask",
        json={"query": query},
        timeout=120,
    )
    ask_response = AskResponse.model_validate_json(response.text)
    lines = [ask_response.answer, ""]
    for source in ask_response.sources:
        lines.append(f"[{source.ref}] {source.url}")
    lines += ["", f"Request ID: {ask_response.request_id}",
              "Reply /found ID or /missed ID"]
    return "\n".join(lines)


def handle_found(request_id: str):
    return handle_feedback(request_id, "FOUND")


def handle_missed(request_id: str):
    return handle_feedback(request_id, "MISSED")


def handle_feedback(request_id: str, feedback: str):
    response = requests.post(
        "http://localhost:8000/feedback",
        json={"request_id": request_id, "feedback": feedback},
        timeout=120,
    )
    if response.status_code == 200:
        return "Recorded"
    return "ID not found"


COMMANDS = {
    "/ask": handle_ask,
    "/found": handle_found,
    "/missed": handle_missed,
}

if __name__ == '__main__':
    get_updates()
