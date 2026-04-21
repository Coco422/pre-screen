from functools import cached_property
from io import BytesIO

from minio import Minio

from pre_screen_common.settings import AppSettings


class MinioStore:
    @cached_property
    def _settings(self) -> AppSettings:
        return AppSettings()

    @cached_property
    def _client(self) -> Minio:
        endpoint = self._settings.minio_endpoint.removeprefix("http://").removeprefix("https://")
        secure = self._settings.minio_endpoint.startswith("https://")
        return Minio(
            endpoint,
            access_key=self._settings.minio_access_key,
            secret_key=self._settings.minio_secret_key,
            secure=secure,
        )

    def put_pdf(self, *, object_key: str, content: bytes, content_type: str) -> str:
        payload = BytesIO(content)
        self._client.put_object(
            self._settings.resume_bucket,
            object_key,
            payload,
            length=len(content),
            content_type=content_type,
        )
        return object_key


minio_store = MinioStore()
