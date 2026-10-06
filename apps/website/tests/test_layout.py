import re

from django.contrib.staticfiles import finders
from django.test import override_settings
from django.urls import reverse


def test_home_page_renders_the_site_layout(client):
    response = client.get(reverse("website:home"))

    assert response.status_code == 200
    assert b'id="main"' in response.content
    assert b"Skip to content" in response.content


@override_settings(WHATSAPP_NUMBER="919876543210", CONTACT_PHONE="+91 98765 43210")
def test_layout_links_to_whatsapp_and_phone(client):
    response = client.get(reverse("website:home"))

    assert response.context["WHATSAPP_URL"].startswith(
        "https://wa.me/919876543210?text=Hello%2C"
    )
    assert b'href="tel:+919876543210"' in response.content


def test_public_pages_load_only_local_scripts(client):
    """The strict CSP allows scripts from our own domain only."""
    response = client.get(reverse("website:home"))
    content = response.content.decode()

    assert "/static/vendor/htmx-4.0.0.min.js" in content
    assert "/static/vendor/alpine-csp-3.17.4.min.js" in content
    assert "<script>" not in content


def test_every_static_file_the_layout_links_to_exists(client):
    """Catches a renamed or missing vendored file before the browser does."""
    response = client.get(reverse("website:home"))
    paths = re.findall(r'(?:src|href)="/static/([^"]+)"', response.content.decode())

    assert paths
    for path in paths:
        if path != "css/site.css":  # built by Tailwind, not committed
            assert finders.find(path), f"static/{path} is missing"
