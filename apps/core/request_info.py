"""The visitor's real IP address, as seen behind Cloudflare and a proxy."""

import ipaddress

from django.conf import settings


def client_ip(request) -> str | None:
    """Return the client's IP address, or None if it isn't a valid address.

    In production, requests reach Django through Cloudflare, so REMOTE_ADDR is
    Cloudflare's address. CLIENT_IP_HEADER (e.g. "HTTP_CF_CONNECTING_IP") names
    the header that carries the real visitor IP. Only set it when the server
    accepts traffic from Cloudflare alone; otherwise anyone could send that
    header and pretend to be any IP.
    """
    header = settings.CLIENT_IP_HEADER or "REMOTE_ADDR"
    value = request.META.get(header, "").strip()
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None
