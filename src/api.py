import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from answers import answer, Answer, Source
from chroma_config import setup_chroma
from chunks import process_document
from digest import digest
from events import record_ask, update_feedback, connect_events, record_find, record_review_event
from fetch import fetch_url
from index import build_index
from init_db import init_db
from logging_config import setup_logging
from model import LLMTimeOutException
from review import select_review, connect_review, review_reason, record_review, record_opened
from schemas import SavedItemDigest, DigestParseError
from storage import save_item, connect, record_fetch, record_digest, save_snapshot
from tools import SearchHit, search_saved
from urls import InvalidUrlError

setup_logging()
logger = logging.getLogger(__name__)

chroma_collection = setup_chroma()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # runs once, before the first request
    yield  # the app serves requests here
    # code after yield would run at shutdown (nothing to do yet)


app = FastAPI(lifespan=lifespan)


class SavedAtOrigin(str, Enum):
    LIVE = "LIVE"
    IMPORT = "IMPORT"
    ORIGINAL = "ORIGINAL"


class Feedback(str, Enum):
    FOUND = "FOUND"
    MISSED = "MISSED"


class SaveRequest(BaseModel):
    url: str
    origin_type: SavedAtOrigin = SavedAtOrigin.LIVE


class SaveResponse(BaseModel):
    item_id: str
    url: str
    status: str
    digest: Optional[SavedItemDigest] = None
    title: Optional[str] = None
    error: Optional[str] = None
    warning: Optional[str] = None


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    request_id: str
    answer: str
    sources: list[Source]


class FeedbackRequest(BaseModel):
    request_id: str
    feedback: Feedback


class FeedbackResponse(BaseModel):
    status: str


class FindRequest(BaseModel):
    query: str
    domain: str | None = None
    since: int | None = None  # saved_day, e.g., 20261101 same as retrieve's saved_day
    until: int | None = None


class FindResponse(BaseModel):
    request_id: str
    hits: list[SearchHit]


class ReviewPick(BaseModel):
    item_id: str
    title: str | None
    url: str
    saved_day: str  # "2026-10-14"
    reason: str


class ReviewResponse(BaseModel):
    request_id: str
    picks: list[ReviewPick]


class OpenedRequest(BaseModel):
    item_id: str


class OpenedResponse(BaseModel):
    status: str


SAVE_MESSAGE = (
    "request_id=%(request_id)s path=/save "
    "status=%(status)s item_id=%(item_id)s "
    "item_status=%(item_status)s "
    "latency_ms=%(latency_ms).2f error=%(error)r"
)

ASK_MESSAGE = "request_id=%(request_id)s path=/ask query_len=%(query_len)d latency_ms=%(latency_ms).2f"

FIND_MESSAGE = "request_id=%(request_id)s path=/find query_len=%(query_len)d latency_ms=%(latency_ms).2f"

REVIEW_MESSAGE = "request_id=%(request_id)s path=/review picks=%(picks)d latency_ms=%(latency_ms).2f"


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
    index_warning = None
    try:
        if not item.url:
            raise HTTPException(status_code=400, detail="Missing URL")

        conn = connect()
        saved_item, created = save_item(conn, item.url, item.origin_type.name)
        result = saved_item

        if not result["content_text"]:
            fetch_result = fetch_url(result["url"])
            snapshot_path = save_snapshot(result["id"], fetch_result.raw_html) if fetch_result.ok else None
            result = record_fetch(
                conn,
                result["id"],
                fetch_result,
                snapshot_path
            )
            if created and result["content_text"]:
                try:
                    process_document([result["id"]])
                    build_index(chroma_collection, conn, item_id=result["id"])
                except Exception as e:
                    logger.exception(str(e))
                    index_warning = "Indexing failed."

        if not result["digest_json"] and result["content_text"]:
            err_msg = None
            summary = None
            try:
                summary = digest(result["content_text"])
            except LLMTimeOutException:
                err_msg = "llm_timeout"
            except DigestParseError as parsing_err:
                err_msg = parsing_err.reason
            except Exception as model_err:  # provider/API error: keep the item and its text, retry later
                logger.exception("digest failed item_id=%s", result["id"])
                err_msg = f"model_error: {type(model_err).__name__}"
            result = record_digest(conn, result["id"], summary, err_msg)

        log_data["item_status"] = result["status"]
        saved_item_digest = SavedItemDigest.model_validate_json(result["digest_json"]) \
            if result["digest_json"] else None
        response = SaveResponse(
            item_id=result["id"],
            url=result["url"],
            title=result["title"],
            digest=saved_item_digest,
            status=result["status"],
            error=result["error"],
            warning=index_warning,
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


@app.post("/ask")
def ask(request: AskRequest) -> AskResponse:
    start = time.perf_counter()
    try:
        result = answer(request.query, chroma_collection)
    except Exception:  # embedding/Chroma/model failure: controlled reply, still recorded as an event
        logger.exception("ask failed")
        result = Answer(answer="Search is not available right now. Please try again later.",
                        sources=[], insufficient_evidence=True, layer="error")
    latency_ms = (time.perf_counter() - start) * 1000
    request_id = str(uuid.uuid4())
    conn = connect_events()
    record_ask(conn, request_id, len(request.query), latency_ms, result)
    logger.info(ASK_MESSAGE, {"request_id": request_id,
                              "query_len": len(request.query),
                              "latency_ms": latency_ms})
    return AskResponse(request_id=request_id, answer=result.answer, sources=result.sources)


@app.post("/feedback")
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    request_id = request.request_id
    conn = connect_events()
    row, updated = update_feedback(conn, request_id, request.feedback.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Unknown request_id")
    return FeedbackResponse(status="ok")


@app.post("/find")
def find(request: FindRequest) -> FindResponse:
    conn = connect_events()
    try:
        start = time.perf_counter()
        try:
            hits = search_saved(query=request.query, collection=chroma_collection, connection=conn,
                                domain=request.domain, since=request.since, until=request.until)
        except Exception as e:
            logger.exception("find failed")
            raise HTTPException(status_code=503, detail="Search is not available right now.") from e
        latency_ms = (time.perf_counter() - start) * 1000
        request_id = str(uuid.uuid4())
        record_find(conn, request_id, len(request.query), latency_ms, hits)
        logger.info(FIND_MESSAGE, {"request_id": request_id,
                                   "query_len": len(request.query),
                                   "latency_ms": latency_ms})
        return FindResponse(request_id=request_id, hits=hits)
    finally:
        conn.close()


@app.post("/review")
def review() -> ReviewResponse:
    conn = connect_review()
    try:
        start = time.perf_counter()
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        selected_reviews = select_review(conn, now)
        picks = [ReviewPick(item_id=selected["id"], title=selected["title"],
                            url=selected["url"], saved_day=selected["saved_at"][:10],
                            reason=review_reason(dict(selected)))
                 for selected in selected_reviews]
        ids = [p.item_id for p in picks]
        latency_ms = (time.perf_counter() - start) * 1000
        record_review(conn, request_id, ids, now)
        record_review_event(conn, request_id, query_len=0, latency_ms=latency_ms, picks=ids)
        logger.info(REVIEW_MESSAGE, {"request_id": request_id,
                                     "picks": len(ids),
                                     "latency_ms": latency_ms})
        return ReviewResponse(request_id=request_id, picks=picks)
    finally:
        conn.close()


@app.post("/opened")
def opened(request: OpenedRequest) -> OpenedResponse:
    conn = connect_review()
    try:
        record_opened(conn, request.item_id, datetime.now(timezone.utc))
        return OpenedResponse(status="ok")
    except ValueError:
        raise HTTPException(status_code=404, detail="Item ID not found")
    finally:
        conn.close()
