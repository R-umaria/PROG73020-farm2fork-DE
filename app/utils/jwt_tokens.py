from __future__ import annotations

import base64
import json
from datetime import UTC, datetime

from app.schemas.auth import DriverJwtPayload


class DriverTokenError(ValueError):
    pass


class DriverTokenExpiredError(DriverTokenError):
    pass


def _base64url_decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(f"{value}{padding}")
    except Exception as exc:
        raise DriverTokenError("Invalid JWT encoding") from exc


def decode_driver_jwt(token: str) -> DriverJwtPayload:
    parts = token.split('.')
    if len(parts) < 2:
        raise DriverTokenError("JWT must include header and payload sections")
    try:
        payload_data = json.loads(_base64url_decode(parts[1]).decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DriverTokenError("JWT payload could not be decoded") from exc

    email = str(payload_data.get('email') or payload_data.get('sub') or payload_data.get('username') or '').strip().lower()
    user_type = str(payload_data.get('user_type') or payload_data.get('role') or '').strip().lower()
    exp = payload_data.get('exp')
    subject_id = payload_data.get('id') or payload_data.get('user_id') or payload_data.get('customer_id')
    name = payload_data.get('name') or payload_data.get('full_name')

    if exp is not None:
        try:
            exp = int(exp)
        except (TypeError, ValueError) as exc:
            raise DriverTokenError("JWT exp claim must be an integer timestamp") from exc

    if subject_id is not None:
        try:
            subject_id = int(subject_id)
        except (TypeError, ValueError):
            subject_id = None

    payload = DriverJwtPayload(email=email, user_type=user_type, exp=exp, subject_id=subject_id, name=name)
    if payload.exp is not None:
        expires_at = datetime.fromtimestamp(payload.exp, tz=UTC)
        if expires_at < datetime.now(tz=UTC):
            raise DriverTokenExpiredError("Driver redirect token has expired")
    return payload
