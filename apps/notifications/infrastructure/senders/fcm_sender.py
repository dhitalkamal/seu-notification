"""FCM push notification sender using Firebase Admin SDK."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")


@lru_cache(maxsize=1)
def _get_app():
    """Initialise Firebase app once per process. Returns None if credentials not configured."""
    if not _CREDENTIALS_PATH or not os.path.exists(_CREDENTIALS_PATH):
        logger.warning("FIREBASE_CREDENTIALS_PATH not set or file missing - FCM push disabled.")
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(_CREDENTIALS_PATH)
        if not firebase_admin._apps:
            return firebase_admin.initialize_app(cred)
        return firebase_admin.get_app()
    except Exception:
        logger.exception("Failed to initialise Firebase app - FCM push disabled.")
        return None


def send_push(*, token: str, title: str, body: str, data: dict | None = None) -> bool:
    """
    Send a single FCM push message to a device token.

    Returns True on success, False if FCM is unconfigured or delivery fails.
    """
    app = _get_app()
    if app is None:
        return False
    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        messaging.send(message, app=app)
        return True
    except Exception:
        logger.exception("FCM push failed for token %s", token[:8])
        return False


def send_push_multicast(
    *, tokens: list[str], title: str, body: str, data: dict | None = None
) -> int:
    """
    Send a push message to multiple device tokens.

    Returns the count of successful deliveries, or 0 if FCM is unconfigured.
    """
    app = _get_app()
    if app is None or not tokens:
        return 0
    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message, app=app)
        return response.success_count
    except Exception:
        logger.exception("FCM multicast failed for %d tokens", len(tokens))
        return 0
