from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    postgres_dsn: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_resumes: str
    ai_api_key: str = ""
    ai_base_url: str = "http://172.16.99.204:3398"
    ai_model: str = "qwen3.6-27b"
    judge0_base_url: str
    # memory: demo_store (default for local demo seed)
    # postgres: durable repositories (production cutover path)
    store_backend: str = "memory"
    bootstrap_admin_username: str = "hr-demo"
    bootstrap_admin_password: str = "demo-pass"
    bootstrap_admin_display_name: str = "Demo HR"

    @property
    def resume_bucket(self) -> str:
        return self.minio_bucket_resumes

    @property
    def use_postgres_store(self) -> bool:
        return self.store_backend.strip().lower() == "postgres"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
