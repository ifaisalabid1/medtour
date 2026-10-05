from urllib.parse import parse_qs, urlsplit

import pytest
from storages.backends.s3 import S3Storage

from config.storage import CACHE_FOREVER, r2_storages

CONFIG = r2_storages(
    account_id="abc123",
    access_key="key-id",
    secret_key="secret",
    public_bucket="medtour-media",
    public_domain="media.medtour.example",
    private_bucket="medtour-private",
)


def make_storage(alias):
    return S3Storage(**CONFIG[alias]["OPTIONS"])


@pytest.mark.parametrize("alias", ["default", "private"])
def test_both_buckets_use_the_r2_endpoint_and_never_overwrite(alias):
    storage = make_storage(alias)

    assert storage.endpoint_url == "https://abc123.r2.cloudflarestorage.com"
    assert storage.file_overwrite is False


def test_public_files_get_plain_cacheable_urls_on_the_media_domain():
    storage = make_storage("default")

    url = storage.url("hospitals/photo.jpg")

    assert url == "https://media.medtour.example/hospitals/photo.jpg"
    assert storage.object_parameters == {"CacheControl": CACHE_FOREVER}


def test_private_file_urls_are_signed_and_expire_quickly():
    storage = make_storage("private")

    url = storage.url("enquiries/report.pdf")

    parts = urlsplit(url)
    query = parse_qs(parts.query)
    assert parts.netloc == "abc123.r2.cloudflarestorage.com"
    assert parts.path == "/medtour-private/enquiries/report.pdf"
    assert "X-Amz-Signature" in query
    assert query["X-Amz-Expires"] == ["300"]
