from datetime import datetime
import time

from flask import current_app, g, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request


def mark_request_start() -> None:
    g.request_started_at = time.perf_counter()


def log_user_activity(status_code: int) -> None:
    started_at = getattr(g, "request_started_at", None)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2) if started_at else None

    user_id = None
    role = "anonymous"
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
        user_id = get_jwt_identity()
        role = claims.get("role") or "anonymous"
    except Exception:
        pass

    query_string = request.query_string.decode("utf-8") if request.query_string else ""
    payload = request.get_json(silent=True) if request.method in {"POST", "PUT", "PATCH", "DELETE"} else None
    payload_keys = ",".join(sorted(payload.keys())) if isinstance(payload, dict) else ""

    log_line = (
        f"{datetime.utcnow().isoformat()}Z | "
        f"user_id={user_id} | role={role} | "
        f"ip={request.remote_addr} | method={request.method} | "
        f"path={request.path} | query={query_string} | status={status_code} | "
        f"duration_ms={duration_ms} | payload_keys={payload_keys}"
    )
    current_app.logger.info("[USER_ACTIVITY] %s", log_line)

