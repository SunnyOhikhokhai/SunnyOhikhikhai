"""Object storage abstraction for uploaded images and documents.

``local`` writes to NIPAM_UPLOAD_DIR (served at /uploads in development; serve
from a CDN/object store in production). ``s3`` uses any S3-compatible store
(AWS S3, Cloudflare R2, DigitalOcean Spaces) and requires boto3.
``vercel_blob`` uses Vercel Blob with the BLOB_READ_WRITE_TOKEN that Vercel
adds when a Blob store is connected to the project.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

import httpx

from ..config import get_settings
from ..errors import ApiError

# Allowed types are detected from file content (magic bytes), never the
# client-supplied filename or content-type.
SIGNATURES: list[tuple[bytes, int, str, str]] = [
    (b"\xff\xd8\xff", 0, "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "png", "image/png"),
    (b"WEBP", 8, "webp", "image/webp"),
    (b"%PDF-", 0, "pdf", "application/pdf"),
]


def detect_type(data: bytes) -> tuple[str, str]:
    for sig, offset, ext, mime in SIGNATURES:
        if data[offset : offset + len(sig)] == sig:
            if ext == "webp" and data[:4] != b"RIFF":
                continue
            return ext, mime
    raise ApiError(415, "unsupported_file", "Only JPEG, PNG, WebP images and PDF documents are allowed.")


def store_upload(data: bytes, folder: str) -> dict:
    s = get_settings()
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise ApiError(413, "file_too_large", f"Files must be {s.max_upload_mb} MB or smaller.")
    if not data:
        raise ApiError(422, "empty_file", "The uploaded file is empty.")
    ext, mime = detect_type(data)
    key = f"{folder}/{secrets.token_hex(16)}.{ext}"

    if s.storage_backend == "vercel_blob":
        url = _put_vercel_blob(key, data, mime)
    elif s.storage_backend == "s3":  # pragma: no cover - requires credentials
        import boto3

        client = boto3.client("s3", region_name=s.s3_region or None, endpoint_url=s.s3_endpoint_url or None)
        client.put_object(Bucket=s.s3_bucket, Key=key, Body=data, ContentType=mime, ACL="public-read")
        url = f"{s.s3_public_url.rstrip('/')}/{key}"
    else:
        path = Path(s.upload_dir) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        url = f"{s.upload_public_url.rstrip('/')}/{key}"
    return {"url": url, "content_type": mime, "size": len(data), "kind": "document" if ext == "pdf" else "image"}


def _put_vercel_blob(key: str, data: bytes, mime: str) -> str:
    token = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
    if not token:
        raise ApiError(503, "storage_unavailable", "File storage is not configured. Connect a Vercel Blob store to the project.")
    r = httpx.put(
        f"https://blob.vercel-storage.com/{key}",
        content=data,
        headers={
            "authorization": f"Bearer {token}",
            "x-api-version": "7",
            "x-content-type": mime,
            "x-add-random-suffix": "0",
            "x-cache-control-max-age": "31536000",
        },
        timeout=30,
    )
    if r.status_code >= 400:
        raise ApiError(502, "storage_failed", "The file could not be stored. Please try again.")
    return r.json()["url"]
