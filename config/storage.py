"""Cloudflare R2 storage settings, kept separate so they can be unit-tested."""

S3_BACKEND = "storages.backends.s3.S3Storage"

# Uploaded files get random names and are never overwritten, so browsers and
# Cloudflare can cache them for a year.
CACHE_FOREVER = "public, max-age=31536000, immutable"

# Links to private files (if ever generated) expire after five minutes.
PRIVATE_LINK_SECONDS = 300


def r2_storages(
    *,
    account_id: str,
    access_key: str,
    secret_key: str,
    public_bucket: str,
    public_domain: str,
    private_bucket: str,
) -> dict:
    """STORAGES entries for R2: a public bucket for images, a private one for
    medical documents. Static files are handled separately."""
    connection = {
        "endpoint_url": f"https://{account_id}.r2.cloudflarestorage.com",
        "access_key": access_key,
        "secret_key": secret_key,
        "region_name": "auto",  # required by the S3 client, ignored by R2
        "signature_version": "s3v4",
        "file_overwrite": False,
    }
    return {
        "default": {
            "BACKEND": S3_BACKEND,
            "OPTIONS": {
                **connection,
                "bucket_name": public_bucket,
                # Served from your own domain through Cloudflare's CDN; no
                # signed URLs needed because these images are public.
                "custom_domain": public_domain,
                "querystring_auth": False,
                "object_parameters": {"CacheControl": CACHE_FOREVER},
            },
        },
        "private": {
            "BACKEND": S3_BACKEND,
            "OPTIONS": {
                **connection,
                "bucket_name": private_bucket,
                "querystring_auth": True,
                "querystring_expire": PRIVATE_LINK_SECONDS,
            },
        },
    }
