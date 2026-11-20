try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing 'slowapi'. Run 'backend/venv/bin/python -m pip install -r backend/requirements.txt'."
    ) from exc

from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
