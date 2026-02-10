import httpx


def create_http_client(**kwargs) -> httpx.AsyncClient:
    defaults = {
        "timeout": 30.0,
        "follow_redirects": True,
    }
    defaults.update(kwargs)
    return httpx.AsyncClient(**defaults)
