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
    ai_base_url: str
    ai_model: str
    judge0_base_url: str

    @property
    def resume_bucket(self) -> str:
        return self.minio_bucket_resumes
