from __future__ import annotations

from datetime import UTC, datetime
import hashlib

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.driver_portal_repository import DriverPortalRepository
from app.schemas.auth import DriverTokenSessionResponse
from app.utils.jwt_tokens import DriverTokenError, decode_driver_jwt


class DriverAccountNotFoundError(ValueError):
    pass


class DriverAuthService:
    def __init__(self, db: Session | None = None):
        self.db: Session = db or SessionLocal()
        self.repo = DriverPortalRepository(self.db)

    def create_session_from_token(self, token: str) -> DriverTokenSessionResponse:
        payload = decode_driver_jwt(token)
        if payload.user_type != 'driver':
            raise DriverTokenError("Redirect token user_type must be 'driver'")

        account = self.repo.get_driver_account_by_email(payload.email)
        if account is None:
            driver_id = payload.subject_id or self._derive_driver_id(payload.email)
            driver_name = (payload.name or payload.email.split('@')[0].replace('.', ' ').replace('_', ' ')).strip().title() or f"Driver {driver_id}"
            account = self.repo.create_or_update_driver_account(
                driver_id=driver_id,
                email=payload.email,
                driver_name=driver_name,
                vehicle_type=settings.driver_auth_default_vehicle_type,
                driver_status='available',
            )

        active_group = self.repo.get_active_route_group_for_driver(account.driver_id)
        return DriverTokenSessionResponse(
            email=account.email,
            user_type=payload.user_type,
            expires_at=datetime.fromtimestamp(payload.exp, tz=UTC) if payload.exp is not None else None,
            driver_id=account.driver_id,
            driver_name=account.driver_name,
            vehicle_type=account.vehicle_type,
            driver_status=account.driver_status,
            active_route_group_id=str(active_group.id) if active_group is not None else None,
            active_route_group_name=active_group.name if active_group is not None else None,
            active_zone_code=active_group.zone_code if active_group is not None else None,
        )

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _derive_driver_id(email: str) -> int:
        digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
        return int(digest[:8], 16)
