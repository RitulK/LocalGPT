import ipaddress
from urllib.parse import urlsplit

from fastapi import HTTPException, Request


def is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


async def require_local_request(request: Request) -> None:
    client_host = request.client.host if request.client else ""
    if not is_loopback_host(client_host):
        raise HTTPException(status_code=403, detail="This operation is available only to local clients.")

    origin = request.headers.get("origin")
    if origin:
        try:
            parsed_origin = urlsplit(origin)
            origin_host = parsed_origin.hostname or ""
        except ValueError:
            parsed_origin = None
            origin_host = ""
        if (
            parsed_origin is None
            or parsed_origin.scheme not in {"http", "https"}
            or not is_loopback_host(origin_host)
        ):
            raise HTTPException(status_code=403, detail="Requests must originate from a local UI.")
