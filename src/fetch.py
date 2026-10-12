from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

TIMEOUT_SECONDS = 10
MAX_BYTES = 2_000_000
MIN_TEXT_CHARS = 200
NOISE_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]


@dataclass
class Page:
    status_code: int
    content_type: str
    body: bytes


@dataclass
class FetchResult:
    ok: bool
    title: Optional[str] = None
    text: Optional[str] = None
    error: Optional[str] = None


# Helper method to download page content with given url
def download(url: str) -> Page:
    body = b""
    with requests.get(url, timeout=TIMEOUT_SECONDS, stream=True,
                      headers={"User-Agent": "ReadLaterAssistant/0.1"}) as response:
        # 2MB at max
        for chunk in response.iter_content(chunk_size=65536):
            body += chunk
            if len(body) > MAX_BYTES:
                break
        return Page(response.status_code, response.headers.get("Content-type"), body)


# Helper method to extract title and main from html
def extract(html: bytes) -> tuple[Optional[str], str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    # Remove useless tags
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    lines = [line.strip() for line in main.get_text("\n").splitlines()]
    return title, "\n".join(line for line in lines if line)


def failed(code: str, detail: str = "") -> FetchResult:
    return FetchResult(ok=False, error=f"{code}: {detail}" if detail else code)


# Download page and parse article with error handling
def fetch_url(url: str, download_page=download) -> FetchResult:
    try:
        page = download_page(url)
    except requests.Timeout:
        return failed("timeout")
    except requests.RequestException as e:
        return failed("network_error", type(e).__name__)

    if page.status_code != 200:
        return failed(f"http_{page.status_code}")
    if "html" not in page.content_type:
        return failed("unsupported_content_type", page.content_type)
    if len(page.body) > MAX_BYTES:
        return failed("too_large", f"more than {MAX_BYTES} bytes")

    title, text = extract(page.body)
    if len(text) < MIN_TEXT_CHARS:
        return failed("too_little_text", f"{len(text)} chars")
    return FetchResult(ok=True, title=title, text=text)
