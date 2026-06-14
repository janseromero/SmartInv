"""ObjectStore implementations: S3/SeaweedFS (MVP) and in-memory (tests)."""

from __future__ import annotations

from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from api.config import Settings, get_settings
from api.contracts.object_store import ObjectNotFoundError


class S3ObjectStore:
    """Object store backed by any S3-compatible service (SeaweedFS, AWS, R2)."""

    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> S3ObjectStore:
        cfg = settings or get_settings()
        client = boto3.client(
            "s3",
            endpoint_url=cfg.s3_endpoint_url,
            aws_access_key_id=cfg.s3_access_key,
            aws_secret_access_key=cfg.s3_secret_key,
            region_name=cfg.s3_region,
            config=Config(s3={"addressing_style": "path"}),
        )
        return cls(client, cfg.s3_bucket)

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        extra = {"ContentType": content_type} if content_type else {}
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                raise ObjectNotFoundError(key) from exc
            raise
        body: bytes = response["Body"].read()
        return body

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError:
            return False
        return True

    def url(self, key: str, *, expires_in: int = 3600) -> str:
        presigned: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return presigned

    def list(self, prefix: str = "") -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return sorted(keys)

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


class InMemoryObjectStore:
    """In-memory object store for tests and contract-compliance checks."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        self._data[key] = data

    def get(self, key: str) -> bytes:
        try:
            return self._data[key]
        except KeyError as exc:
            raise ObjectNotFoundError(key) from exc

    def exists(self, key: str) -> bool:
        return key in self._data

    def url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"memory://{key}"

    def list(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._data if k.startswith(prefix))

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
