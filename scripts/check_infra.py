"""Smoke-test connectivity to the local SmartInv infrastructure.

Verifies that the configured Postgres (with required extensions), Redis, and
S3-compatible object store are reachable. This is the CV1.E4 Done Condition
check. Exits non-zero if any check fails.
"""

from __future__ import annotations

import pathlib
import sys

# Make the api package importable without requiring an editable install.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "services" / "api" / "src"))

import boto3
import psycopg
import redis
from api.config import Settings, get_settings
from botocore.config import Config

REQUIRED_PG_EXTENSIONS = {"vector", "pg_trgm"}


def check_postgres(settings: Settings) -> None:
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension")
            installed = {row[0] for row in cur.fetchall()}
    missing = REQUIRED_PG_EXTENSIONS - installed
    if missing:
        raise RuntimeError(f"Postgres reachable but missing extensions: {sorted(missing)}")


def check_redis(settings: Settings) -> None:
    client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=5)
    if not client.ping():
        raise RuntimeError("Redis did not respond to PING")


def check_object_store(settings: Settings) -> None:
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1}),
    )
    client.list_buckets()


def main() -> int:
    settings = get_settings()
    checks = (
        ("postgres", check_postgres),
        ("redis", check_redis),
        ("object-store", check_object_store),
    )
    failed = False
    for name, check in checks:
        try:
            check(settings)
        except Exception as exc:  # noqa: BLE001 — report every failure, don't abort early
            print(f"FAIL  {name}: {exc}")
            failed = True
        else:
            print(f"OK    {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
