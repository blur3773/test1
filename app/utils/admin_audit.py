from datetime import datetime

from flask import current_app, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request


def log_admin_action(action: str, details: str = "") -> None:
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
    except Exception:
        return

    if claims.get("role") != "admin":
        return

    user_id = get_jwt_identity()
    log_line = (
        f"{datetime.utcnow().isoformat()}Z | "
        f"user_id={user_id} | "
        f"ip={request.remote_addr} | "
        f"method={request.method} | "
        f"path={request.path} | "
        f"action={action} | "
        f"details={details}"
    )

    current_app.logger.info("[ADMIN_AUDIT] %s", log_line)

