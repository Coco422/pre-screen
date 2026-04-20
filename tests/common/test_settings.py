from pre_screen_common.settings import AppSettings


def test_settings_build_service_urls_from_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv(
        "POSTGRES_DSN", "postgresql+psycopg://postgres:postgres@localhost:5432/prescreen"
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_BUCKET_RESUMES", "resumes")
    monkeypatch.setenv("AI_BASE_URL", "https://aiapi.szmckj.cn")
    monkeypatch.setenv("AI_MODEL", "qwen3.6-35b-a3b")
    monkeypatch.setenv("JUDGE0_BASE_URL", "http://judge0:2358")

    settings = AppSettings()

    assert settings.app_env == "local"
    assert settings.resume_bucket == "resumes"
    assert settings.ai_base_url == "https://aiapi.szmckj.cn"
    assert settings.judge0_base_url == "http://judge0:2358"
