"""Server-side verification of Cloudflare Turnstile tokens (spam protection)."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TIMEOUT_SECONDS = 5
MAX_TOKEN_LENGTH = 2048


def verify_turnstile(token: str, remote_ip: str | None) -> bool:
    """True only if Cloudflare confirms the visitor passed the challenge.

    Fails closed: any network error or unexpected reply counts as a failure,
    so an outage at Cloudflare can't open the form to bots.
    """
    if not token or len(token) > MAX_TOKEN_LENGTH:
        return False
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    try:
        response = requests.post(SITEVERIFY_URL, data=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException, ValueError:
        logger.exception("Turnstile verification request failed")
        return False
    if not result.get("success"):
        logger.info("Turnstile rejected a token: %s", result.get("error-codes"))
        return False
    return True
