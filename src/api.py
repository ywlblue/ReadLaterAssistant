from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fetch import fetch_url
from urls import normalize_url, InvalidUrlError
from storage import save_item, connect, record_fetch


class SaveRequest(BaseModel):
    url: str


class SaveResponse(BaseModel):
    item_id: str
    url: str
    status: str
    title: Optional[str] = None
    error: Optional[str] = None


app = FastAPI()


@app.post("/save")
def save_url(item: SaveRequest) -> SaveResponse:
    url = item.url
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")
    try:
        normalized_url = normalize_url(url)
        conn = connect()
        saved_item, created = save_item(conn, normalized_url)
        if saved_item["status"] != "fetched":
            result = record_fetch(conn, saved_item["id"], fetch_url(saved_item["url"]))
        else:
            result = saved_item
    except InvalidUrlError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something wrong with saving url: {str(e)}")
    return SaveResponse(
        item_id=result["id"], url=result["url"], title=result["title"], status=result["status"], error=result["error"])
