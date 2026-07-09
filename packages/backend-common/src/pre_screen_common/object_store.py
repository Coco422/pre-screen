"""MinIO object storage helpers for durable resume PDFs."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from pre_screen_common.settings import AppSettings, get_settings


class ObjectStore:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings

    @property
    def settings(self) -> AppSettings:
        return self._settings or get_settings()

    @property
    def client(self) -> Minio:
        endpoint = self.settings.minio_endpoint.removeprefix("http://").removeprefix("https://")
        secure = self.settings.minio_endpoint.startswith("https://")
        return Minio(
            endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=secure,
        )

    def ensure_bucket(self) -> str:
        bucket = self.settings.resume_bucket
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except S3Error:
            # Bucket may already exist or race on concurrent ensure.
            if not self.client.bucket_exists(bucket):
                raise
        return bucket

    def put_bytes(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> tuple[str, str]:
        bucket = self.ensure_bucket()
        self.client.put_object(
            bucket,
            object_key,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )
        return bucket, object_key

    def get_bytes(self, *, bucket: str, object_key: str) -> bytes:
        response = self.client.get_object(bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


@lru_cache(maxsize=1)
def get_object_store() -> ObjectStore:
    return ObjectStore()
