"""
Signed cookie-based session store.

Stores all session data in the cookie itself (HMAC-signed, not encrypted).
No server-side storage needed. Good for small sessions (< 4KB).

WARNING: Data is visible to the client (base64 encoded, not encrypted).
Do not store sensitive information in cookie sessions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Optional

from .base import SessionInterface


class CookieSessionStore(SessionInterface):
    """Signed cookie-based session store.

    Session data is serialized to JSON, base64-encoded, and HMAC-signed.
    The "session_id" for this backend is the signed cookie value itself.

    Args:
        secret: Secret key for HMAC signing. Must be kept private.
        max_age: Maximum session age in seconds (default: 3600).
                 Set to 0 for sessions that never expire (browser session).

    Example::

        store = CookieSessionStore(secret="my-secret-key", max_age=1800)
    """

    def __init__(self, secret: str, max_age: int = 3600):
        if not secret:
            raise ValueError("CookieSessionStore requires a non-empty secret")
        self._secret = secret.encode("utf-8")
        self._max_age = max_age

    def _sign(self, payload: bytes) -> str:
        """Create HMAC-SHA256 signature for the payload."""
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def _verify(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def encode(self, data: dict[str, Any]) -> str:
        """Encode and sign session data into a cookie value.

        Format: base64(json(data)).signature

        Args:
            data: Session data dict to encode.

        Returns:
            Signed cookie value string.
        """
        # Embed timestamp for expiry checking
        wrapper = {"_ts": time.time(), "_data": data}
        payload = base64.urlsafe_b64encode(
            json.dumps(wrapper, separators=(",", ":")).encode("utf-8")
        )
        sig = self._sign(payload)
        return f"{payload.decode('utf-8')}.{sig}"

    def decode(self, cookie_value: str) -> Optional[dict[str, Any]]:
        """Decode and verify a signed cookie value.

        Args:
            cookie_value: The signed cookie string.

        Returns:
            The session data dict, or None if invalid/expired.
        """
        if "." not in cookie_value:
            return None

        parts = cookie_value.rsplit(".", 1)
        if len(parts) != 2:
            return None

        payload_str, signature = parts
        payload = payload_str.encode("utf-8")

        if not self._verify(payload, signature):
            return None

        try:
            raw = base64.urlsafe_b64decode(payload)
            wrapper = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return None

        if not isinstance(wrapper, dict) or "_data" not in wrapper:
            return None

        # Check expiry
        if self._max_age > 0:
            ts = wrapper.get("_ts", 0)
            if time.time() - ts > self._max_age:
                return None

        return wrapper["_data"]

    # -- SessionInterface --

    async def load(self, session_id: str) -> Optional[dict[str, Any]]:
        """Load session data from a signed cookie value.

        For cookie sessions, the session_id IS the cookie value.
        """
        return self.decode(session_id)

    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        """No-op for cookie sessions — data is stored in the cookie.

        The actual encoding happens in the middleware when setting the cookie.
        """
        pass

    async def delete(self, session_id: str) -> None:
        """No-op for cookie sessions — deletion happens by clearing the cookie."""
        pass
