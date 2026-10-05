import pytest
from django.test import RequestFactory

from apps.core.request_info import client_ip


@pytest.fixture
def request_from():
    def make(**meta):
        return RequestFactory().get("/", **meta)

    return make


def test_uses_remote_addr_by_default(request_from, settings):
    settings.CLIENT_IP_HEADER = ""

    assert client_ip(request_from(REMOTE_ADDR="203.0.113.7")) == "203.0.113.7"


def test_uses_the_configured_proxy_header(request_from, settings):
    settings.CLIENT_IP_HEADER = "HTTP_CF_CONNECTING_IP"
    request = request_from(
        REMOTE_ADDR="172.68.1.1", HTTP_CF_CONNECTING_IP="198.51.100.20"
    )

    assert client_ip(request) == "198.51.100.20"


@pytest.mark.parametrize("value", ["", "not-an-ip", "1.2.3.4, 5.6.7.8"])
def test_invalid_addresses_become_none(request_from, settings, value):
    settings.CLIENT_IP_HEADER = "HTTP_CF_CONNECTING_IP"

    assert client_ip(request_from(HTTP_CF_CONNECTING_IP=value)) is None
