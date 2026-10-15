import logging
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fetch import fetch_url
from logging_config import setup_logging
from urls import normalize_url, InvalidUrlError
from storage import save_item, connect, record_fetch

setup_logging()
logger = logging.getLogger(__name__)


class SaveRequest(BaseModel):
    url: str


class SaveResponse(BaseModel):
    item_id: str
    url: str
    status: str
    title: Optional[str] = None
    error: Optional[str] = None


app = FastAPI()

SAVE_MESSAGE = (
    "request_id=%(request_id)s path=/save "
    "status=%(status)s item_id=%(item_id)s "
    "item_status=%(item_status)s "
    "latency_ms=%(latency_ms).2f error=%(error)r"
)


@app.post("/save")
def save_url(item: SaveRequest) -> SaveResponse:
    start = time.perf_counter()
    log_data = {
        "request_id": str(uuid.uuid4()),
        "status": 500,
        "item_id": None,
        "item_status": None,
        "error": None,
    }
    unexpected_error = None

    try:
        if not item.url:
            raise HTTPException(status_code=400, detail="Missing URL")

        normalized_url = normalize_url(item.url)
        conn = connect()
        saved_item, created = save_item(conn, normalized_url)

        if saved_item["status"] != "fetched":
            result = record_fetch(
                conn,
                saved_item["id"],
                fetch_url(saved_item["url"]),
            )
        else:
            result = saved_item

        log_data["item_status"] = result["status"]

        response = SaveResponse(
            item_id=result["id"],
            url=result["url"],
            title=result["title"],
            status=result["status"],
            error=result["error"],
        )
        log_data["item_id"] = result["id"]
        log_data["error"] = result["error"]
        log_data["status"] = 200
        return response

    except InvalidUrlError as e:
        log_data["status"] = 400
        log_data["error"] = str(e)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URL: {item.url}",
        ) from e

    except HTTPException as e:
        log_data["status"] = e.status_code
        log_data["error"] = str(e.detail)
        raise

    except Exception as e:
        log_data["error"] = str(e)
        unexpected_error = e
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while saving the URL.",
        ) from e

    finally:
        log_data["latency_ms"] = (time.perf_counter() - start) * 1000
        level = logging.ERROR if log_data["status"] >= 500 else logging.INFO

        logger.log(
            level,
            SAVE_MESSAGE,
            log_data,
            exc_info=unexpected_error,
        )
