import logging
import os

import requests
from dotenv import load_dotenv

from api import SaveResponse, AskResponse, FindResponse, ReviewResponse
from logging_config import setup_logging
from routing import route, USAGE
from tools import MAX_DISTANCE

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
                send_message(dispatch(text), chat_id)


def dispatch(text: str) -> str:
    """One user message in, one reply out. Shared by the bot loop and eval_workflow."""
    r = route(text)
    handler = COMMANDS.get(r.command)
    try:
        return handler(r.arg) if handler else USAGE
    except requests.Timeout:
        logger.error("API timeout command=%s", r.command)
        return "The server took too long to reply. Please try again."
    except requests.ConnectionError:
        logger.error("API unreachable command=%s", r.command)
        return "Cannot reach the server. Is the API running?"
    except Exception as e:
        logger.error(str(e))
        return f"Encounter an error: {e}"


def api_error(response) -> str | None:
    """A short reply for a non-200 API response, or None when the response is OK."""
    if response.status_code == 200:
        return None
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    return f"Error: {detail or f'server returned {response.status_code}'}"


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
    if err := api_error(response):
        return err
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
    if err := api_error(response):
        return err
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


def handle_find(query: str):
    response = requests.post(
        "http://localhost:8000/find",
        json={"query": query},
        timeout=120,
    )
    if err := api_error(response):
        return err
    find_response = FindResponse.model_validate_json(response.text)
    hits = find_response.hits
    if len(hits) == 0:
        return "No saved item matched. Try more specific words."

    def fmt(i, h):
        return f"{i}. {h.title} ({h.saved_day})\n   {h.url}"

    strong = [h for h in hits if h.distance <= MAX_DISTANCE]
    weak = [h for h in hits if h.distance > MAX_DISTANCE]
    lines = [fmt(i, h) for i, h in enumerate(strong, 1)]
    if weak:
        lines += ["", "Weaker matches:"] + [fmt(i, h) for i, h in enumerate(weak, len(strong) + 1)]
    lines += ["", f"Request ID: {find_response.request_id}", "Reply /found ID or /missed ID"]
    return "\n".join(lines)


def handle_review(_: str):
    response = requests.post(
        "http://localhost:8000/review",
        timeout=120,
    )
    if err := api_error(response):
        return err
    review_response = ReviewResponse.model_validate_json(response.text)
    picks = review_response.picks
    if len(picks) == 0:
        return "Nothing to review right now. All recent items are opened or were suggested in the last 14 days."
    lines = []
    for i, pick in enumerate(picks, 1):
        lines += [f"{i}. {pick.title or pick.url} ({pick.saved_day})",
                  f"   {pick.url}",
                  f"   Why: {pick.reason}",
                  f"   ID: {pick.item_id}",
                  ""]
    lines += [f"Request ID: {review_response.request_id}", "Reply /opened ID to record opened"]
    return "\n".join(lines)


def handle_opened(item_id: str):
    response = requests.post(
        "http://localhost:8000/opened",
        json={"item_id": item_id},
        timeout=120,
    )
    if response.status_code == 200:
        return "Marked as opened"
    if response.status_code == 404:
        return "Item ID not found"
    response.raise_for_status()


COMMANDS = {
    "/ask": handle_ask,
    "/found": handle_found,
    "/missed": handle_missed,
    "save": handle_save,
    "/find": handle_find,
    "/review": handle_review,
    "/opened": handle_opened
}

if __name__ == '__main__':
    get_updates()
