import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"fbclid", "gclid"}
DEFAULT_PORTS = {"http": 80, "https": 443}


class InvalidUrlError(ValueError):
    pass


def normalize_url(url: str) -> str:
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError as e:
        raise InvalidUrlError(f"cannot parse URL: {url!r}") from e

    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if scheme not in DEFAULT_PORTS or not host:
        raise InvalidUrlError(f"not a http(s) URL: {url!r}")

    netloc = host if port in (None, DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    path = parts.path.rstrip("/")
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(params))

    return urlunsplit((scheme, netloc, path, query, ""))


# Create hash value to prevent duplicates
def make_item_id(normalized_url: str) -> str:
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:16]


def domain_of(normalized_url: str) -> str:
    return urlsplit(normalized_url).hostname or ""
