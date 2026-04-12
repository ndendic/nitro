"""
Nitro Auth — Core authentication service.

Framework-agnostic, stateless. Uses stdlib only (hashlib, hmac, secrets, base64, json).
No external JWT library required.

For production with python-jose, subclass AuthService and override
_create_token / decode_token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from .models import User


class TokenPayload(BaseModel):
    sub: str              # user id
    exp: float            # unix timestamp
    type: str = "access"  # "access" or "refresh"
    roles: list[str] = []


class AuthService:
    """Framework-agnostic authentication service.

    Uses HMAC-SHA256 signed tokens (no external JWT dependency needed).
    For production, install python-jose and use JWTAuthService instead.

    Args:
        secret: Secret key used to sign tokens. Keep this private.
        access_ttl_minutes: Lifetime of access tokens (default: 30 min).
        refresh_ttl_minutes: Lifetime of refresh tokens (default: 7 days).
    """

    def __init__(
        self,
        secret: str,
        access_ttl_minutes: int = 30,
        refresh_ttl_minutes: int = 10080,
    ):
        self.secret = secret
        self.access_ttl = access_ttl_minutes
        self.refresh_ttl = refresh_ttl_minutes

    # ------------------------------------------------------------------
    # Password hashing (stdlib PBKDF2-SHA256, no passlib needed)
    # ------------------------------------------------------------------

    def hash_password(self, password: str) -> str:
        """Hash a password with PBKDF2-SHA256. No external dependencies needed."""
        salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return f"pbkdf2:sha256:{salt}:{dk.hex()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against its stored hash."""
        parts = hashed.split(":")
        if len(parts) != 4 or parts[0] != "pbkdf2":
            return False
        _, algo, salt, stored_hash = parts
        dk = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), 100_000)
        return hmac.compare_digest(dk.hex(), stored_hash)

    # ------------------------------------------------------------------
    # Token creation and verification (HMAC-SHA256 signed)
    # ------------------------------------------------------------------

    def _create_token(
        self,
        user_id: str,
        token_type: str,
        ttl_minutes: int,
        roles: list[str] | None = None,
    ) -> str:
        """Build a base64url-encoded, HMAC-signed token."""
        payload = {
            "sub": user_id,
            "exp": (
                datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
            ).timestamp(),
            "type": token_type,
            "roles": roles or [],
        }
        data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig = hmac.new(self.secret.encode(), data.encode(), hashlib.sha256).hexdigest()
        return f"{data}.{sig}"

    def create_access_token(self, user_id: str, roles: list[str] | None = None) -> str:
        """Create a short-lived access token for the given user."""
        return self._create_token(user_id, "access", self.access_ttl, roles or [])

    def create_refresh_token(self, user_id: str) -> str:
        """Create a long-lived refresh token (no roles embedded)."""
        return self._create_token(user_id, "refresh", self.refresh_ttl)

    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and verify a token.

        Returns a TokenPayload if valid and not expired, or None otherwise.
        """
        try:
            data, sig = token.rsplit(".", 1)
            expected_sig = hmac.new(
                self.secret.encode(), data.encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(base64.urlsafe_b64decode(data))
            if payload["exp"] < datetime.now(timezone.utc).timestamp():
                return None
            return TokenPayload(**payload)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Higher-level user operations
    # ------------------------------------------------------------------

    def register(
        self,
        email: str,
        password: str,
        display_name: str = "",
        roles: list[str] | None = None,
    ) -> "User":
        """Register a new user. Raises ValueError if email already taken.

        Returns the saved User entity.
        """
        from .models import User

        if User.find_by(email=email):
            raise ValueError(f"User with email {email} already exists")
        user = User(
            email=email,
            hashed_password=self.hash_password(password),
            display_name=display_name or email.split("@")[0],
            roles=",".join(roles) if roles else "",
        )
        user.save()
        return user

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> Optional[tuple["User", str, str]]:
        """Authenticate a user by email and password.

        Returns (user, access_token, refresh_token) on success, or None on failure.
        Failure reasons: unknown email, wrong password, or inactive account.
        """
        from .models import User

        result = User.find_by(email=email)
        # find_by may return a list (multiple matches) or a single entity
        if not result:
            return None
        user: User = result[0] if isinstance(result, list) else result
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        user.last_login = datetime.now(timezone.utc)
        user.save()
        access = self.create_access_token(str(user.id), user.role_list)
        refresh = self.create_refresh_token(str(user.id))
        return user, access, refresh
