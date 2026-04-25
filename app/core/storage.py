"""
Attachment storage: local disk (default) or S3-compatible when S3_BUCKET is set.
On AWS EC2, omit AWS_ACCESS_KEY_ID/SECRET and use an instance role.
"""
import logging
import uuid
from pathlib import Path

from app.config import get_settings

log = logging.getLogger(__name__)


def save_attachment_file(
    data: bytes,
    *,
    workspace_id: str,
    original_name: str,
    ext: str,
    content_type: str | None,
) -> str:
    """
    Persist bytes and return a value to store in Attachment.storage_path.
    - Local: relative path under upload_dir
    - S3: s3://bucket/prefix/key
    """
    settings = get_settings()
    safe_ext = ext if ext.startswith(".") else f".{ext}" if ext else ""
    file_id = f"{uuid.uuid4().hex}{safe_ext}"
    rel_key = f"{workspace_id}/{file_id}"

    if settings.s3_bucket:
        pfx = settings.s3_prefix.strip().strip("/")
        key = f"{pfx}/{rel_key}" if pfx else rel_key
        return _save_s3(data, key=key, content_type=content_type)

    root = Path(settings.upload_dir)
    (root / workspace_id).mkdir(parents=True, exist_ok=True)
    full = root / workspace_id / file_id
    full.write_bytes(data)
    return str(Path(workspace_id) / file_id).replace("\\", "/")


def _save_s3(data: bytes, *, key: str, content_type: str | None) -> str:
    import boto3
    from botocore.config import Config

    s = get_settings()
    config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
    kw: dict = {"region_name": s.aws_region, "config": config}
    if s.s3_endpoint_url:
        kw["endpoint_url"] = s.s3_endpoint_url
    if s.aws_access_key_id and s.aws_secret_access_key:
        client = boto3.client(
            "s3",
            aws_access_key_id=s.aws_access_key_id,
            aws_secret_access_key=s.aws_secret_access_key,
            **kw,
        )
    else:
        client = boto3.client("s3", **kw)

    extra: dict = {}
    if content_type:
        extra["ContentType"] = content_type
    client.put_object(Bucket=s.s3_bucket, Key=key, Body=data, **extra)
    uri = f"s3://{s.s3_bucket}/{key}"
    log.info("s3_uploaded key=%s bytes=%s", key, len(data))
    return uri
