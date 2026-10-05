import pytest
import requests

from apps.leads import turnstile
from apps.leads.turnstile import verify_turnstile


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture
def siteverify(monkeypatch):
    """Replace the Cloudflare call; set `reply` to choose the answer."""

    class Siteverify:
        reply = {"success": True}
        requests_sent = []

    def fake_post(url, data, timeout):
        Siteverify.requests_sent.append(data)
        if isinstance(Siteverify.reply, Exception):
            raise Siteverify.reply
        return FakeResponse(Siteverify.reply)

    Siteverify.requests_sent = []
    monkeypatch.setattr(turnstile.requests, "post", fake_post)
    return Siteverify


def test_accepted_token_passes_and_sends_secret_and_ip(siteverify, settings):
    settings.TURNSTILE_SECRET_KEY = "secret-key"

    assert verify_turnstile("token", "203.0.113.7") is True
    assert siteverify.requests_sent == [
        {"secret": "secret-key", "response": "token", "remoteip": "203.0.113.7"}
    ]


def test_rejected_token_fails(siteverify):
    siteverify.reply = {"success": False, "error-codes": ["invalid-input-response"]}

    assert verify_turnstile("token", None) is False


def test_network_errors_fail_closed(siteverify):
    siteverify.reply = requests.ConnectionError("Cloudflare unreachable")

    assert verify_turnstile("token", None) is False


@pytest.mark.parametrize("token", ["", "x" * 2049])
def test_missing_or_oversized_tokens_fail_without_calling_cloudflare(siteverify, token):
    assert verify_turnstile(token, None) is False
    assert siteverify.requests_sent == []
