"""Create the SmartInv object-store bucket(s). Idempotent.

Run after ``docker compose up`` (``make dev-up`` does this automatically).
Retries until the SeaweedFS S3 endpoint accepts connections, then ensures the
configured bucket exists.
"""

from __future__ import annotations

import pathlib
import sys
import time

# Make the api package importable without requiring an editable install.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

import boto3
from api.config import get_settings
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def main() -> int:
    settings = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1}),
    )

    deadline = time.time() + 60.0
    while True:
        try:
            existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
            break
        except (BotoCoreError, ClientError) as exc:
            if time.time() > deadline:
                print(f"object store not reachable at {settings.s3_endpoint_url}: {exc}")
                return 1
            time.sleep(2.0)

    if settings.s3_bucket in existing:
        print(f"bucket already present: {settings.s3_bucket}")
    else:
        client.create_bucket(Bucket=settings.s3_bucket)
        print(f"created bucket: {settings.s3_bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
