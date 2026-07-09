from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from pre_screen_common.db import db_connection
from pre_screen_common.security import hash_password, hash_token, new_token, verify_password
from pre_screen_common.settings import AppSettings, get_settings

SESSION_TTL = timedelta(days=7)


class AuthRepository:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    def ensure_bootstrap_admin(self) -> None:
        settings = self._settings or get_settings()
        with db_connection(settings=settings) as conn:
            row = conn.execute(
                text("select id from auth.users where username = :username"),
                {"username": settings.bootstrap_admin_username},
            ).first()
            if row is not None:
                return
            conn.execute(
                text(
                    """
                    insert into auth.users (username, password_hash, display_name, role)
                    values (:username, :password_hash, :display_name, 'hr')
                    """
                ),
                {
                    "username": settings.bootstrap_admin_username,
                    "password_hash": hash_password(settings.bootstrap_admin_password),
                    "display_name": settings.bootstrap_admin_display_name,
                },
            )

    def login(self, username: str, password: str) -> dict[str, Any]:
        with db_connection(settings=self._settings) as conn:
            user = conn.execute(
                text(
                    """
                    select id, username, password_hash, display_name, role, is_active
                    from auth.users
                    where username = :username
                    """
                ),
                {"username": username},
            ).mappings().first()
            if user is None or not user["is_active"]:
                raise PermissionError("Invalid username or password.")
            if not verify_password(password, user["password_hash"]):
                raise PermissionError("Invalid username or password.")

            token = new_token(24)
            expires_at = datetime.now(UTC) + SESSION_TTL
            conn.execute(
                text(
                    """
                    insert into auth.sessions (user_id, token_hash, expires_at)
                    values (:user_id, :token_hash, :expires_at)
                    """
                ),
                {
                    "user_id": user["id"],
                    "token_hash": hash_token(token),
                    "expires_at": expires_at,
                },
            )
            return {
                "token": token,
                "user": {
                    "user_id": f"u-{user['id']}",
                    "username": user["username"],
                    "display_name": user["display_name"],
                    "role": user["role"],
                },
            }

    def get_current_user(self, token: str) -> dict[str, Any]:
        with db_connection(settings=self._settings) as conn:
            row = conn.execute(
                text(
                    """
                    select u.id, u.username, u.display_name, u.role, u.is_active, s.expires_at, s.id as session_id
                    from auth.sessions s
                    join auth.users u on u.id = s.user_id
                    where s.token_hash = :token_hash
                    """
                ),
                {"token_hash": hash_token(token)},
            ).mappings().first()
            if row is None or not row["is_active"]:
                raise PermissionError("Admin session is invalid.")
            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < datetime.now(UTC):
                conn.execute(
                    text("delete from auth.sessions where id = :session_id"),
                    {"session_id": row["session_id"]},
                )
                raise PermissionError("Admin session is invalid.")
            conn.execute(
                text("update auth.sessions set last_seen_at = now() where id = :session_id"),
                {"session_id": row["session_id"]},
            )
            return {
                "user_id": f"u-{row['id']}",
                "username": row["username"],
                "display_name": row["display_name"],
                "role": row["role"],
            }


def ensure_auth_ready(settings: AppSettings | None = None) -> None:
    AuthRepository(settings=settings).ensure_bootstrap_admin()
