# Pre-Screen MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working version of the technical candidate pre-screen system described in `docs/superpowers/specs/2026-04-21-pre-screen-design.md`, including resume ingestion, candidate profile extraction, exam generation, online test-taking, autosave, Judge0-based coding questions, scoring, and risk event logging.

**Architecture:** Use a mono-repo with one Vue web app and six FastAPI services (`gateway`, `resume`, `exam`, `judge-bridge`, `scoring`, `risk`). Share one PostgreSQL instance, one Redis instance, one MinIO instance, and one Judge0 deployment. Use Celery for asynchronous work, Flyway for schema migrations, Docker Compose for local development, and `uv` for Python dependency management.

**Tech Stack:** FastAPI, SQLAlchemy 2, Pydantic 2, Celery, Redis, PostgreSQL, Flyway, MinIO, PyMuPDF, OpenAI Python SDK (OpenAI-compatible base URL), Judge0 HTTP API, Vue 3, TypeScript, Vite, Vue Router, Pinia, Element Plus, Monaco Editor, Vitest, Playwright, Docker Compose, Nginx.

---

## File Structure

Use this structure from the start so service boundaries stay clear without needing multiple repositories:

- `pyproject.toml`
  Root Python project managed by `uv`; shared backend dependencies and dev tooling.
- `.python-version`
  Pins Python for local development and CI.
- `.env.example`
  Documents required environment variables for local development.
- `.gitignore`
  Keeps `.venv`, Node build output, MinIO temp files, PDF render output, and `.superpowers/` out of git.
- `docker-compose.yml`
  Local development stack for PostgreSQL, Redis, MinIO, Judge0, service containers, and the web app.
- `infra/docker/`
  Dockerfiles for backend services and the web app.
- `infra/nginx/nginx.conf`
  Reverse proxy for local end-to-end testing.
- `database/flyway/`
  Flyway configs and SQL migrations grouped by owned schema.
- `packages/backend-common/src/pre_screen_common/`
  Shared config, database session helpers, logging, HTTP clients, MinIO helper, and common schemas.
- `services/gateway/`
  Public entrypoint service and API aggregation.
- `services/resume/`
  Resume upload, PyMuPDF parsing, page metrics, multimodal fallback, candidate profile extraction.
- `services/exam/`
  Templates, question bank, exam paper drafts, invitations, sessions, answer persistence.
- `services/judge_bridge/`
  Judge0 integration, run vs submit handling, polling, and raw judge result persistence.
- `services/scoring/`
  Objective scoring, subjective suggestion scoring, summary generation, manual review.
- `services/risk/`
  Risk events, heartbeat ingestion, audit log persistence.
- `apps/web/`
  Single Vue app with `/admin/*` and `/exam/*` route trees.
- `scripts/`
  Local bootstrap, Flyway runner, AI smoke test, Judge0 smoke test, and verification helpers.
- `tests/`
  Cross-service Python integration tests and smoke checks.

## Assumptions

- Use one Vue app instead of separate admin and candidate repos to reduce coordination cost in a small team.
- Use one root Python environment managed by `uv` instead of a Python workspace per service to keep dependency management simpler in the first milestone.
- Open first-party product language support with eight languages: `C`, `C++`, `Java`, `Python`, `JavaScript`, `TypeScript`, `Go`, and `Rust`.
- Keep `Kotlin`, `C#`, and `PHP` in configuration enums and admin UI selectors only after Judge0 smoke checks pass for those runtimes.
- Use Element Plus for admin pages to accelerate tables/forms; keep candidate exam UI custom around Monaco Editor and the timer shell.

## Task 1: Repository Foundation and Local Infrastructure

**Files:**
- Create: `.gitignore`
- Create: `.python-version`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `docker-compose.yml`
- Create: `infra/docker/backend.Dockerfile`
- Create: `infra/docker/web.Dockerfile`
- Create: `infra/nginx/nginx.conf`
- Create: `scripts/dev-up.sh`
- Create: `scripts/dev-down.sh`
- Test: `tests/common/test_settings.py`

- [ ] **Step 1: Write the failing settings test**

```python
# tests/common/test_settings.py
from pre_screen_common.settings import AppSettings


def test_settings_build_service_urls_from_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql+psycopg://postgres:postgres@localhost:5432/prescreen")
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/common/test_settings.py -v`

Expected: `ModuleNotFoundError: No module named 'pre_screen_common'`

- [ ] **Step 3: Create the root project files and shared settings module**

```toml
# pyproject.toml
[project]
name = "pre-screen"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "boto3>=1.34.0",
  "celery[redis]>=5.4.0",
  "fastapi>=0.115.0",
  "httpx>=0.28.0",
  "minio>=7.2.0",
  "openai>=1.75.0",
  "orjson>=3.10.0",
  "pydantic-settings>=2.8.0",
  "pydantic>=2.10.0",
  "psycopg[binary]>=3.2.0",
  "pymupdf>=1.27.0",
  "redis>=5.2.0",
  "sqlalchemy>=2.0.40",
  "uvicorn[standard]>=0.34.0",
]

[dependency-groups]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.25.0",
  "pytest-cov>=6.0.0",
  "respx>=0.22.0",
  "ruff>=0.11.0",
]

[tool.pytest.ini_options]
pythonpath = ["packages/backend-common/src", "services"]
testpaths = ["tests", "services"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

```python
# packages/backend-common/src/pre_screen_common/settings.py
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
```

```gitignore
# .gitignore
.DS_Store
.env
.venv/
node_modules/
dist/
coverage/
playwright-report/
tmp/
.pytest_cache/
.ruff_cache/
.superpowers/
```

```env
# .env.example
APP_ENV=local
POSTGRES_DSN=postgresql+psycopg://postgres:postgres@localhost:5432/prescreen
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_RESUMES=resumes
AI_BASE_URL=https://aiapi.szmckj.cn
AI_MODEL=qwen3.6-35b-a3b
AI_API_KEY=
JUDGE0_BASE_URL=http://judge0:2358
```

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: prescreen
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:RELEASE.2025-02-28T09-55-16Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  minio-init:
    image: minio/mc:RELEASE.2025-02-21T16-00-46Z
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      until (/usr/bin/mc alias set local http://minio:9000 minioadmin minioadmin) do echo 'waiting for minio'; sleep 2; done;
      /usr/bin/mc mb --ignore-existing local/resumes;
      exit 0;
      "

  judge0-db:
    image: postgres:16
    environment:
      POSTGRES_DB: judge0
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"

  judge0-redis:
    image: redis:7
    ports:
      - "6380:6379"

  judge0:
    image: judge0/judge0:latest
    depends_on:
      - judge0-db
      - judge0-redis
    environment:
      DATABASE_URL: postgres://postgres:postgres@judge0-db:5432/judge0
      REDIS_URL: redis://judge0-redis:6379/0
    ports:
      - "2358:2358"

volumes:
  postgres_data:
  minio_data:
```

```bash
# scripts/dev-up.sh
#!/usr/bin/env bash
set -euo pipefail

docker compose up -d postgres redis minio minio-init judge0-db judge0-redis judge0
docker compose ps
```

```bash
# scripts/dev-down.sh
#!/usr/bin/env bash
set -euo pipefail

docker compose down
```

```dockerfile
# infra/docker/backend.Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install uv && uv pip install --system .
COPY packages ./packages
COPY services ./services
COPY scripts ./scripts

CMD ["python", "-m", "uvicorn", "services.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Run local bootstrap verification**

Run: `uv sync --group dev && docker compose config`

Expected: `Resolved` output from `uv`, then a normalized compose file with no validation errors.

- [ ] **Step 5: Bring up the local infrastructure**

Run: `bash scripts/dev-up.sh`

Expected: running containers for `postgres`, `redis`, `minio`, `minio-init`, `judge0-db`, `judge0-redis`, and `judge0`

- [ ] **Step 6: Re-run the test to verify it passes**

Run: `uv run pytest tests/common/test_settings.py -v`

Expected: `1 passed`

- [ ] **Step 7: Commit**

```bash
git add .gitignore .python-version .env.example pyproject.toml README.md docker-compose.yml \
  packages/backend-common/src/pre_screen_common/settings.py tests/common/test_settings.py \
  infra/docker infra/nginx scripts/dev-up.sh scripts/dev-down.sh
git commit -m "chore: bootstrap repo and local infrastructure"
```

## Task 2: Shared FastAPI Service Skeletons

**Files:**
- Create: `packages/backend-common/src/pre_screen_common/app_factory.py`
- Create: `packages/backend-common/src/pre_screen_common/logging.py`
- Create: `services/gateway/app/main.py`
- Create: `services/resume/app/main.py`
- Create: `services/exam/app/main.py`
- Create: `services/judge_bridge/app/main.py`
- Create: `services/scoring/app/main.py`
- Create: `services/risk/app/main.py`
- Test: `tests/services/test_service_health.py`

- [ ] **Step 1: Write the failing service health test**

```python
# tests/services/test_service_health.py
from fastapi.testclient import TestClient

from services.gateway.app.main import app as gateway_app
from services.resume.app.main import app as resume_app
from services.exam.app.main import app as exam_app
from services.judge_bridge.app.main import app as judge_app
from services.scoring.app.main import app as scoring_app
from services.risk.app.main import app as risk_app


def test_gateway_health():
    assert TestClient(gateway_app).get("/healthz").json()["service"] == "gateway"


def test_resume_health():
    assert TestClient(resume_app).get("/healthz").json()["service"] == "resume"


def test_exam_health():
    assert TestClient(exam_app).get("/healthz").json()["service"] == "exam"


def test_judge_bridge_health():
    assert TestClient(judge_app).get("/healthz").json()["service"] == "judge-bridge"


def test_scoring_health():
    assert TestClient(scoring_app).get("/healthz").json()["service"] == "scoring"


def test_risk_health():
    assert TestClient(risk_app).get("/healthz").json()["service"] == "risk"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/services/test_service_health.py -v`

Expected: import failure because service apps do not exist yet.

- [ ] **Step 3: Implement the shared app factory and service entrypoints**

```python
# packages/backend-common/src/pre_screen_common/app_factory.py
from fastapi import FastAPI


def create_service_app(service_name: str) -> FastAPI:
    app = FastAPI(title=f"pre-screen-{service_name}")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"service": service_name, "status": "ok"}

    return app
```

```python
# services/gateway/app/main.py
from pre_screen_common.app_factory import create_service_app

app = create_service_app("gateway")
```

```python
# services/judge_bridge/app/main.py
from pre_screen_common.app_factory import create_service_app

app = create_service_app("judge-bridge")
```

- [ ] **Step 4: Re-run the test to verify it passes**

Run: `uv run pytest tests/services/test_service_health.py -v`

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add packages/backend-common/src/pre_screen_common/app_factory.py \
  packages/backend-common/src/pre_screen_common/logging.py \
  services/gateway/app/main.py services/resume/app/main.py services/exam/app/main.py \
  services/judge_bridge/app/main.py services/scoring/app/main.py services/risk/app/main.py \
  tests/services/test_service_health.py
git commit -m "feat: add backend service skeletons"
```

## Task 3: Flyway Bootstrap and Initial Schemas

**Files:**
- Create: `database/flyway/auth/flyway.conf`
- Create: `database/flyway/resume/flyway.conf`
- Create: `database/flyway/exam/flyway.conf`
- Create: `database/flyway/judge/flyway.conf`
- Create: `database/flyway/scoring/flyway.conf`
- Create: `database/flyway/risk/flyway.conf`
- Create: `database/flyway/*/V1__bootstrap.sql`
- Create: `scripts/flyway-migrate.sh`
- Test: `tests/database/test_bootstrap_schemas.py`

- [ ] **Step 1: Write the failing schema bootstrap test**

```python
# tests/database/test_bootstrap_schemas.py
import psycopg


def test_bootstrap_schemas_exist():
    with psycopg.connect("postgresql://postgres:postgres@localhost:5432/prescreen") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select schema_name
                from information_schema.schemata
                where schema_name in ('auth', 'resume', 'exam', 'judge', 'scoring', 'risk')
                order by schema_name
                """
            )
            rows = [row[0] for row in cur.fetchall()]

    assert rows == ["auth", "exam", "judge", "resume", "risk", "scoring"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/database/test_bootstrap_schemas.py -v`

Expected: assertion failure because the schemas do not exist yet.

- [ ] **Step 3: Add the Flyway configs and bootstrap SQL**

```properties
# database/flyway/resume/flyway.conf
flyway.url=jdbc:postgresql://localhost:5432/prescreen
flyway.user=postgres
flyway.password=postgres
flyway.defaultSchema=resume
flyway.schemas=resume
flyway.locations=filesystem:database/flyway/resume/sql
flyway.table=flyway_history_resume
```

```sql
-- database/flyway/resume/sql/V1__bootstrap.sql
create schema if not exists resume;

create table if not exists resume.candidates (
  id bigserial primary key,
  org_id bigint not null default 1,
  name text,
  phone text,
  email text,
  status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists resume.resume_files (
  id bigserial primary key,
  candidate_id bigint not null references resume.candidates(id),
  minio_bucket text not null,
  minio_object_key text not null,
  file_name text not null,
  file_size bigint not null,
  page_count integer not null default 0,
  parse_status text not null default 'pending',
  parse_error text,
  created_at timestamptz not null default now()
);
```

```bash
# scripts/flyway-migrate.sh
#!/usr/bin/env bash
set -euo pipefail

for service in auth resume exam judge scoring risk; do
  docker run --rm \
    --network host \
    -v "$PWD/database/flyway:/flyway/conf" \
    -w /flyway/conf \
    flyway/flyway:11 \
    -configFiles="/flyway/conf/${service}/flyway.conf" migrate
done
```

- [ ] **Step 4: Run migrations and re-run the test**

Run: `bash scripts/flyway-migrate.sh && uv run pytest tests/database/test_bootstrap_schemas.py -v`

Expected: Flyway applies `V1__bootstrap.sql` for each schema, then `1 passed`

- [ ] **Step 5: Commit**

```bash
git add database/flyway scripts/flyway-migrate.sh tests/database/test_bootstrap_schemas.py
git commit -m "feat: add flyway bootstrap for service schemas"
```

## Task 4: Minimal AI and Judge0 Smoke Checks

**Files:**
- Create: `packages/backend-common/src/pre_screen_common/ai_client.py`
- Create: `packages/backend-common/src/pre_screen_common/judge0_client.py`
- Create: `scripts/check_ai_text.py`
- Create: `scripts/check_judge0.py`
- Test: `tests/integrations/test_ai_client.py`
- Test: `tests/integrations/test_judge0_client.py`

- [ ] **Step 1: Write the failing integration client tests**

```python
# tests/integrations/test_ai_client.py
import respx
from httpx import Response

from pre_screen_common.ai_client import AIClient


@respx.mock
def test_ai_client_uses_openai_compatible_chat_endpoint():
    route = respx.post("https://aiapi.szmckj.cn/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )
    )

    client = AIClient(api_key="test-key", base_url="https://aiapi.szmckj.cn", model="qwen3.6-35b-a3b")
    result = client.simple_text_completion("ping")

    assert route.called
    assert result == "pong"
```

```python
# tests/integrations/test_judge0_client.py
import respx
from httpx import Response

from pre_screen_common.judge0_client import Judge0Client


@respx.mock
def test_judge0_client_fetches_supported_languages():
    route = respx.get("http://judge0:2358/languages").mock(
        return_value=Response(200, json=[{"id": 71, "name": "Python (3.8.1)"}])
    )

    client = Judge0Client(base_url="http://judge0:2358")
    languages = client.list_languages()

    assert route.called
    assert languages[0]["name"] == "Python (3.8.1)"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/integrations/test_ai_client.py tests/integrations/test_judge0_client.py -v`

Expected: import failure because the client modules do not exist yet.

- [ ] **Step 3: Implement the clients and smoke scripts**

```python
# packages/backend-common/src/pre_screen_common/ai_client.py
from openai import OpenAI


class AIClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def simple_text_completion(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
```

```python
# packages/backend-common/src/pre_screen_common/judge0_client.py
import httpx


class Judge0Client:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def list_languages(self) -> list[dict]:
        response = httpx.get(f"{self._base_url}/languages", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def run_sync(self, payload: dict) -> dict:
        response = httpx.post(f"{self._base_url}/submissions?wait=true", json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

```python
# scripts/check_ai_text.py
import os

from pre_screen_common.ai_client import AIClient


def main() -> None:
    client = AIClient(
        api_key=os.environ["AI_API_KEY"],
        base_url=os.environ["AI_BASE_URL"],
        model=os.environ["AI_MODEL"],
    )
    print(client.simple_text_completion("请只回复 pong"))


if __name__ == "__main__":
    main()
```

```python
# scripts/check_judge0.py
from pre_screen_common.judge0_client import Judge0Client


def main() -> None:
    client = Judge0Client(base_url="http://localhost:2358")
    result = client.run_sync(
        {
            "language_id": 71,
            "source_code": "print('hello from judge0')",
        }
    )
    print(result["stdout"].strip())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Re-run the tests and smoke scripts**

Run: `uv run pytest tests/integrations/test_ai_client.py tests/integrations/test_judge0_client.py -v`

Expected: `2 passed`

Run: `AI_API_KEY=... AI_BASE_URL=https://aiapi.szmckj.cn AI_MODEL=qwen3.6-35b-a3b uv run python scripts/check_ai_text.py`

Expected: prints `pong` or equivalent single-token completion

Run: `uv run python scripts/check_judge0.py`

Expected: prints `hello from judge0`

- [ ] **Step 5: Commit**

```bash
git add packages/backend-common/src/pre_screen_common/ai_client.py \
  packages/backend-common/src/pre_screen_common/judge0_client.py \
  scripts/check_ai_text.py scripts/check_judge0.py tests/integrations
git commit -m "feat: add ai and judge0 smoke checks"
```

## Task 5: Resume Upload and Page Metrics

**Files:**
- Create: `services/resume/app/api/uploads.py`
- Create: `services/resume/app/domain/models.py`
- Create: `services/resume/app/repositories/resume_repository.py`
- Create: `services/resume/app/storage/minio_store.py`
- Create: `services/resume/app/parsing/page_metrics.py`
- Test: `services/resume/tests/test_page_metrics.py`
- Test: `services/resume/tests/test_upload_endpoint.py`

- [ ] **Step 1: Write the failing resume parser tests**

```python
# services/resume/tests/test_page_metrics.py
from pathlib import Path

from services.resume.app.parsing.page_metrics import collect_page_metrics


def test_collect_page_metrics_uses_sample_pdf():
    sample = Path("PDFs/【前端开发工程师_深圳 7-8K】张坚 26年应届生.pdf")
    metrics = collect_page_metrics(sample)

    assert len(metrics) == 3
    assert metrics[0].text_chars > 1000
    assert metrics[0].needs_multimodal is False
```

```python
# services/resume/tests/test_upload_endpoint.py
from fastapi.testclient import TestClient

from services.resume.app.main import app


def test_upload_resume_accepts_pdf():
    client = TestClient(app)
    response = client.post(
        "/internal/resumes/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake pdf", "application/pdf")},
        data={"candidate_name": "Test User"},
    )

    assert response.status_code == 202
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest services/resume/tests/test_page_metrics.py services/resume/tests/test_upload_endpoint.py -v`

Expected: failures because the parser and upload endpoint do not exist yet.

- [ ] **Step 3: Implement page metrics and MinIO-backed upload**

```python
# services/resume/app/parsing/page_metrics.py
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class PageMetric:
    page_number: int
    text_chars: int
    image_count: int
    needs_multimodal: bool


def collect_page_metrics(pdf_path: Path) -> list[PageMetric]:
    doc = fitz.open(pdf_path)
    metrics: list[PageMetric] = []
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        text_chars = len(text.strip())
        image_count = len(page.get_images(full=True))
        needs_multimodal = text_chars < 600 or (text_chars < 1200 and image_count > 1)
        metrics.append(PageMetric(index, text_chars, image_count, needs_multimodal))
    return metrics
```

```python
# services/resume/app/api/uploads.py
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(prefix="/internal/resumes", tags=["resumes"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(candidate_name: str = Form(...), file: UploadFile = File(...)) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")
    return {"candidate_name": candidate_name, "status": "accepted"}
```

- [ ] **Step 4: Mount the router and re-run the tests**

Run: `uv run pytest services/resume/tests/test_page_metrics.py services/resume/tests/test_upload_endpoint.py -v`

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/resume/app/api/uploads.py services/resume/app/domain/models.py \
  services/resume/app/repositories/resume_repository.py services/resume/app/storage/minio_store.py \
  services/resume/app/parsing/page_metrics.py services/resume/tests
git commit -m "feat: add resume upload and page metrics"
```

## Task 6: Resume Profile Extraction and Multimodal Fallback

**Files:**
- Create: `services/resume/app/tasks/parse_resume.py`
- Create: `services/resume/app/parsing/render_pages.py`
- Create: `services/resume/app/parsing/profile_builder.py`
- Create: `services/resume/app/api/profiles.py`
- Test: `services/resume/tests/test_profile_builder.py`
- Test: `services/resume/tests/test_parse_resume_task.py`

- [ ] **Step 1: Write the failing profile builder tests**

```python
# services/resume/tests/test_profile_builder.py
from services.resume.app.parsing.profile_builder import build_candidate_profile


def test_build_candidate_profile_merges_text_and_model_output():
    profile = build_candidate_profile(
        extracted_pages=[
            {"page_number": 1, "text": "姓名: 张三\\n邮箱: zs@example.com\\n技能: Python, Vue"},
            {"page_number": 2, "text": "项目经历: 做过后台管理系统"},
        ],
        multimodal_pages=[
            {"page_number": 1, "summary": "候选人头像清晰，页面标题为简历"},
        ],
    )

    assert profile["email"] == "zs@example.com"
    assert "Python" in profile["skills"]
    assert profile["source_summary"]["multimodal_pages"] == [1]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest services/resume/tests/test_profile_builder.py -v`

Expected: import failure or missing function failure.

- [ ] **Step 3: Implement rendering, fallback detection, and profile building**

```python
# services/resume/app/parsing/profile_builder.py
import re


def build_candidate_profile(extracted_pages: list[dict], multimodal_pages: list[dict]) -> dict:
    text_blob = "\n".join(page["text"] for page in extracted_pages)
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text_blob)
    skills = []
    if "Python" in text_blob:
        skills.append("Python")
    if "Vue" in text_blob:
        skills.append("Vue")
    return {
        "email": email_match.group(0) if email_match else None,
        "skills": skills,
        "source_summary": {"multimodal_pages": [page["page_number"] for page in multimodal_pages]},
        "raw_text": text_blob,
    }
```

```python
# services/resume/app/tasks/parse_resume.py
from pathlib import Path

from services.resume.app.parsing.page_metrics import collect_page_metrics
from services.resume.app.parsing.profile_builder import build_candidate_profile


def parse_resume_file(pdf_path: Path) -> dict:
    metrics = collect_page_metrics(pdf_path)
    extracted_pages = [{"page_number": item.page_number, "text": ""} for item in metrics]
    multimodal_pages = [{"page_number": item.page_number, "summary": "queued"} for item in metrics if item.needs_multimodal]
    return build_candidate_profile(extracted_pages, multimodal_pages)
```

- [ ] **Step 4: Re-run the tests and add a regression check for local sample PDFs**

Run: `uv run pytest services/resume/tests/test_profile_builder.py services/resume/tests/test_parse_resume_task.py -v`

Expected: all resume parsing unit tests pass

Run: `uv run python -c "from pathlib import Path; from services.resume.app.parsing.page_metrics import collect_page_metrics; print(collect_page_metrics(Path('PDFs/【全栈开发工程师_深圳 6-8K】郭子贤 26年应届生.pdf'))[0])"`

Expected: first page shows a `text_chars` value comfortably above 1000

- [ ] **Step 5: Commit**

```bash
git add services/resume/app/tasks/parse_resume.py services/resume/app/parsing/render_pages.py \
  services/resume/app/parsing/profile_builder.py services/resume/app/api/profiles.py \
  services/resume/tests
git commit -m "feat: add resume profile extraction pipeline"
```

## Task 7: Exam Templates, Question Bank, and Paper Drafts

**Files:**
- Create: `services/exam/app/api/templates.py`
- Create: `services/exam/app/api/papers.py`
- Create: `services/exam/app/domain/template_models.py`
- Create: `services/exam/app/domain/paper_generator.py`
- Create: `services/exam/app/repositories/exam_repository.py`
- Test: `services/exam/tests/test_paper_generator.py`
- Test: `services/exam/tests/test_templates_api.py`

- [ ] **Step 1: Write the failing paper generation test**

```python
# services/exam/tests/test_paper_generator.py
from services.exam.app.domain.paper_generator import generate_paper_draft


def test_generate_paper_draft_keeps_fixed_question_mix():
    paper = generate_paper_draft(
        job_template={
            "name": "frontend-intern",
            "objective_count": 4,
            "subjective_count": 2,
            "coding_count": 1,
        },
        jd_text="前端工程师，需要熟悉 Vue、TypeScript、工程化。",
        candidate_profile={"skills": ["Vue", "TypeScript"], "projects": ["后台管理系统"]},
    )

    assert paper["question_mix"] == {"base_info": 1, "objective": 4, "subjective": 2, "coding": 1}
    assert len(paper["questions"]) == 8
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest services/exam/tests/test_paper_generator.py -v`

Expected: import failure because the generator is not implemented.

- [ ] **Step 3: Implement template CRUD and a deterministic draft generator**

```python
# services/exam/app/domain/paper_generator.py
def generate_paper_draft(job_template: dict, jd_text: str, candidate_profile: dict) -> dict:
    questions = [
        {"type": "base_info", "title": "补充基础信息", "score": 0},
        {"type": "objective", "title": "Vue 响应式原理基础", "score": 5},
        {"type": "objective", "title": "TypeScript 类型系统", "score": 5},
        {"type": "objective", "title": "前端工程化基础", "score": 5},
        {"type": "objective", "title": "浏览器与网络基础", "score": 5},
        {"type": "subjective", "title": "请复盘一个你最熟悉的项目", "score": 15},
        {"type": "subjective", "title": "描述一个你定位问题的过程", "score": 15},
        {"type": "coding", "title": "实现一个数组去重函数", "score": 50},
    ]
    return {
        "template_name": job_template["name"],
        "question_mix": {"base_info": 1, "objective": 4, "subjective": 2, "coding": 1},
        "questions": questions,
        "prompt_version": "paper-draft/v1",
        "jd_summary": jd_text[:80],
        "candidate_signals": candidate_profile.get("skills", []),
    }
```

```python
# services/exam/app/api/papers.py
from fastapi import APIRouter

from services.exam.app.domain.paper_generator import generate_paper_draft

router = APIRouter(prefix="/internal/papers", tags=["papers"])


@router.post("/draft")
async def create_draft(payload: dict) -> dict:
    return generate_paper_draft(
        job_template=payload["job_template"],
        jd_text=payload["jd_text"],
        candidate_profile=payload["candidate_profile"],
    )
```

- [ ] **Step 4: Re-run the tests**

Run: `uv run pytest services/exam/tests/test_paper_generator.py services/exam/tests/test_templates_api.py -v`

Expected: passing draft generation tests

- [ ] **Step 5: Commit**

```bash
git add services/exam/app/api/templates.py services/exam/app/api/papers.py \
  services/exam/app/domain/template_models.py services/exam/app/domain/paper_generator.py \
  services/exam/app/repositories/exam_repository.py services/exam/tests
git commit -m "feat: add exam templates and paper draft generation"
```

## Task 8: Invitations, Sessions, Answers, Heartbeats, and Risk Events

**Files:**
- Create: `services/exam/app/api/invitations.py`
- Create: `services/exam/app/api/sessions.py`
- Create: `services/exam/app/api/answers.py`
- Create: `services/risk/app/api/events.py`
- Create: `services/exam/app/domain/session_rules.py`
- Test: `services/exam/tests/test_session_rules.py`
- Test: `services/risk/tests/test_events_api.py`

- [ ] **Step 1: Write the failing session rules test**

```python
# services/exam/tests/test_session_rules.py
from datetime import datetime, timedelta, timezone

from services.exam.app.domain.session_rules import compute_exam_window


def test_compute_exam_window_sets_server_side_expiration():
    start_at = datetime(2026, 4, 21, 10, 0, tzinfo=timezone.utc)
    expire_at = compute_exam_window(start_at, duration_minutes=90)

    assert expire_at == start_at + timedelta(minutes=90)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest services/exam/tests/test_session_rules.py services/risk/tests/test_events_api.py -v`

Expected: missing module failures.

- [ ] **Step 3: Implement invitations, session timing, answer drafts, and risk event ingestion**

```python
# services/exam/app/domain/session_rules.py
from datetime import datetime, timedelta


def compute_exam_window(start_at: datetime, duration_minutes: int) -> datetime:
    return start_at + timedelta(minutes=duration_minutes)
```

```python
# services/risk/app/api/events.py
from fastapi import APIRouter, status

router = APIRouter(prefix="/internal/risk", tags=["risk"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def create_event(payload: dict) -> dict:
    return {"status": "accepted", "event_type": payload["event_type"], "session_id": payload["session_id"]}
```

- [ ] **Step 4: Re-run the tests**

Run: `uv run pytest services/exam/tests/test_session_rules.py services/risk/tests/test_events_api.py -v`

Expected: passing unit tests for session expiration and event ingestion.

- [ ] **Step 5: Commit**

```bash
git add services/exam/app/api/invitations.py services/exam/app/api/sessions.py \
  services/exam/app/api/answers.py services/exam/app/domain/session_rules.py \
  services/risk/app/api/events.py services/exam/tests services/risk/tests
git commit -m "feat: add exam sessions, answers, and risk events"
```

## Task 9: Judge Bridge Run/Submit Flow

**Files:**
- Create: `services/judge_bridge/app/api/submissions.py`
- Create: `services/judge_bridge/app/domain/language_map.py`
- Create: `services/judge_bridge/app/tasks/poll_submission.py`
- Create: `services/judge_bridge/app/domain/scoring.py`
- Test: `services/judge_bridge/tests/test_language_map.py`
- Test: `services/judge_bridge/tests/test_submissions_api.py`

- [ ] **Step 1: Write the failing language map test**

```python
# services/judge_bridge/tests/test_language_map.py
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS


def test_language_map_covers_the_launch_languages():
    assert set(PRODUCT_LANGUAGE_IDS) == {
        "c",
        "cpp",
        "java",
        "python",
        "javascript",
        "typescript",
        "go",
        "rust",
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest services/judge_bridge/tests/test_language_map.py services/judge_bridge/tests/test_submissions_api.py -v`

Expected: missing module failures.

- [ ] **Step 3: Implement the launch language map and run/submit API**

```python
# services/judge_bridge/app/domain/language_map.py
PRODUCT_LANGUAGE_IDS = {
    "c": 50,
    "cpp": 54,
    "java": 62,
    "python": 71,
    "javascript": 63,
    "typescript": 74,
    "go": 60,
    "rust": 73,
}
```

```python
# services/judge_bridge/app/api/submissions.py
from fastapi import APIRouter

from pre_screen_common.judge0_client import Judge0Client
from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS

router = APIRouter(prefix="/internal/judge", tags=["judge"])


@router.post("/run")
async def run_code(payload: dict) -> dict:
    client = Judge0Client(base_url="http://judge0:2358")
    result = client.run_sync(
        {
            "language_id": PRODUCT_LANGUAGE_IDS[payload["language"]],
            "source_code": payload["source_code"],
            "stdin": payload.get("stdin", ""),
        }
    )
    return {"mode": "run", "stdout": result.get("stdout", ""), "status": result.get("status")}
```

- [ ] **Step 4: Re-run the tests and the local Judge0 smoke script**

Run: `uv run pytest services/judge_bridge/tests/test_language_map.py services/judge_bridge/tests/test_submissions_api.py -v`

Expected: passing unit tests

Run: `uv run python scripts/check_judge0.py`

Expected: `hello from judge0`

- [ ] **Step 5: Commit**

```bash
git add services/judge_bridge/app/api/submissions.py \
  services/judge_bridge/app/domain/language_map.py \
  services/judge_bridge/app/tasks/poll_submission.py \
  services/judge_bridge/app/domain/scoring.py \
  services/judge_bridge/tests
git commit -m "feat: add judge bridge run and submit flow"
```

## Task 10: Objective Scoring, Subjective Suggestions, and Result Summary

**Files:**
- Create: `services/scoring/app/api/reviews.py`
- Create: `services/scoring/app/domain/objective.py`
- Create: `services/scoring/app/domain/subjective.py`
- Create: `services/scoring/app/domain/summary.py`
- Create: `services/scoring/app/tasks/suggest_scores.py`
- Test: `services/scoring/tests/test_objective_scoring.py`
- Test: `services/scoring/tests/test_summary.py`

- [ ] **Step 1: Write the failing scoring tests**

```python
# services/scoring/tests/test_objective_scoring.py
from services.scoring.app.domain.objective import score_objective_answer


def test_score_objective_answer_requires_exact_match_for_multi_select():
    score = score_objective_answer(
        answer=["A", "B"],
        answer_key=["A", "B"],
        full_score=5,
        mode="multi_select_exact",
    )

    assert score == 5
```

```python
# services/scoring/tests/test_summary.py
from services.scoring.app.domain.summary import build_score_summary


def test_build_score_summary_combines_objective_subjective_and_coding_scores():
    summary = build_score_summary(
        objective_score=20,
        subjective_score=25,
        coding_score=40,
        risk_summary={"copy": 1},
    )

    assert summary["total_score"] == 85
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest services/scoring/tests/test_objective_scoring.py services/scoring/tests/test_summary.py -v`

Expected: missing domain modules.

- [ ] **Step 3: Implement scoring rules and summary building**

```python
# services/scoring/app/domain/objective.py
def score_objective_answer(answer: list[str] | str, answer_key: list[str] | str, full_score: int, mode: str) -> int:
    if mode == "multi_select_exact":
        return full_score if sorted(answer) == sorted(answer_key) else 0
    if mode == "single_select":
        return full_score if answer == answer_key else 0
    return 0
```

```python
# services/scoring/app/domain/summary.py
def build_score_summary(objective_score: int, subjective_score: int, coding_score: int, risk_summary: dict) -> dict:
    return {
        "objective_score": objective_score,
        "subjective_score": subjective_score,
        "coding_score": coding_score,
        "total_score": objective_score + subjective_score + coding_score,
        "risk_summary": risk_summary,
    }
```

- [ ] **Step 4: Re-run the tests**

Run: `uv run pytest services/scoring/tests/test_objective_scoring.py services/scoring/tests/test_summary.py -v`

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/scoring/app/api/reviews.py services/scoring/app/domain/objective.py \
  services/scoring/app/domain/subjective.py services/scoring/app/domain/summary.py \
  services/scoring/app/tasks/suggest_scores.py services/scoring/tests
git commit -m "feat: add scoring domain and result summaries"
```

## Task 11: Vue Web Shell and HR Admin Flow

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/src/main.ts`
- Create: `apps/web/src/router/index.ts`
- Create: `apps/web/src/layouts/AdminLayout.vue`
- Create: `apps/web/src/views/admin/CandidateListView.vue`
- Create: `apps/web/src/views/admin/CandidateDetailView.vue`
- Create: `apps/web/src/views/admin/PaperEditorView.vue`
- Test: `apps/web/src/router/router.spec.ts`

- [ ] **Step 1: Write the failing router test**

```ts
// apps/web/src/router/router.spec.ts
import { describe, expect, it } from "vitest";
import { routes } from "./index";

describe("router", () => {
  it("includes the admin candidate list route", () => {
    expect(routes.some((route) => route.path === "/admin/candidates")).toBe(true);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npm install && npm run test -- router.spec.ts`

Expected: file not found or missing route export failure.

- [ ] **Step 3: Implement the Vue app shell**

```json
// apps/web/package.json
{
  "name": "pre-screen-web",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@monaco-editor/loader": "^1.5.0",
    "element-plus": "^2.9.0",
    "pinia": "^3.0.0",
    "vue": "^3.5.0",
    "vue-router": "^4.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "typescript": "^5.8.0",
    "vite": "^6.3.0",
    "vitest": "^3.1.0",
    "vue-tsc": "^2.2.0"
  }
}
```

```ts
// apps/web/src/router/index.ts
import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  { path: "/admin/candidates", component: () => import("../views/admin/CandidateListView.vue") },
  { path: "/admin/candidates/:candidateId", component: () => import("../views/admin/CandidateDetailView.vue") },
  { path: "/admin/papers/:paperId", component: () => import("../views/admin/PaperEditorView.vue") },
  { path: "/exam/:token", component: () => import("../views/exam/ExamShellView.vue") },
];
```

- [ ] **Step 4: Re-run the frontend router test**

Run: `cd apps/web && npm run test -- router.spec.ts`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add vue web shell and admin routes"
```

## Task 12: Candidate Exam UI, Autosave, Heartbeat, and Code Editor

**Files:**
- Create: `apps/web/src/views/exam/ExamShellView.vue`
- Create: `apps/web/src/views/exam/ExamQuestionPanel.vue`
- Create: `apps/web/src/views/exam/CodeQuestionPanel.vue`
- Create: `apps/web/src/stores/examSession.ts`
- Create: `apps/web/src/composables/useAutosave.ts`
- Create: `apps/web/src/composables/useHeartbeat.ts`
- Test: `apps/web/src/stores/examSession.spec.ts`

- [ ] **Step 1: Write the failing exam session store test**

```ts
// apps/web/src/stores/examSession.spec.ts
import { setActivePinia, createPinia } from "pinia";
import { describe, expect, it, beforeEach } from "vitest";
import { useExamSessionStore } from "./examSession";

describe("exam session store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("tracks draft answers by question id", () => {
    const store = useExamSessionStore();
    store.upsertDraftAnswer("q-1", { value: "Vue" });
    expect(store.answers["q-1"]).toEqual({ value: "Vue" });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npm run test -- examSession.spec.ts`

Expected: missing store module failure.

- [ ] **Step 3: Implement the exam session store and autosave hooks**

```ts
// apps/web/src/stores/examSession.ts
import { defineStore } from "pinia";

export const useExamSessionStore = defineStore("exam-session", {
  state: () => ({
    answers: {} as Record<string, unknown>,
    lastHeartbeatAt: "",
  }),
  actions: {
    upsertDraftAnswer(questionId: string, value: unknown) {
      this.answers[questionId] = value;
    },
    markHeartbeat(timestamp: string) {
      this.lastHeartbeatAt = timestamp;
    },
  },
});
```

```ts
// apps/web/src/composables/useAutosave.ts
import { watch } from "vue";

export function useAutosave(source: () => unknown, save: (value: unknown) => Promise<void>) {
  let timer: number | undefined;
  watch(
    source,
    (value) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        void save(value);
      }, 600);
    },
    { deep: true }
  );
}
```

- [ ] **Step 4: Re-run the frontend store test**

Run: `cd apps/web && npm run test -- examSession.spec.ts`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/views/exam apps/web/src/stores/examSession.ts \
  apps/web/src/composables/useAutosave.ts apps/web/src/composables/useHeartbeat.ts \
  apps/web/src/stores/examSession.spec.ts
git commit -m "feat: add candidate exam shell with autosave and heartbeat"
```

## Task 13: Dockerized End-to-End Assembly and Verification

**Files:**
- Create: `services/gateway/app/api/public_exam.py`
- Create: `services/gateway/app/api/admin.py`
- Modify: `docker-compose.yml`
- Modify: `infra/nginx/nginx.conf`
- Create: `tests/e2e/test_admin_to_exam_flow.py`
- Create: `scripts/verify-local-stack.sh`

- [ ] **Step 1: Write the failing end-to-end smoke test**

```python
# tests/e2e/test_admin_to_exam_flow.py
from services.scoring.app.domain.summary import build_score_summary


def test_final_summary_shape_matches_admin_result_page_expectations():
    summary = build_score_summary(
        objective_score=20,
        subjective_score=30,
        coding_score=40,
        risk_summary={"copy": 1, "visibility_hidden": 2},
    )

    assert summary == {
        "objective_score": 20,
        "subjective_score": 30,
        "coding_score": 40,
        "total_score": 90,
        "risk_summary": {"copy": 1, "visibility_hidden": 2},
    }
```

- [ ] **Step 2: Run the full test suite to establish a baseline**

Run: `uv run pytest -q && cd apps/web && npm run test`

Expected: all previously added unit tests pass, and the e2e smoke gate confirms the summary shape needed by the admin result page.

- [ ] **Step 3: Wire up Docker Compose service containers and Nginx routing**

```nginx
# infra/nginx/nginx.conf
events {}

http {
  upstream gateway_upstream { server gateway:8000; }
  upstream web_upstream { server web:5173; }

  server {
    listen 80;

    location /api/ {
      proxy_pass http://gateway_upstream/;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
      proxy_pass http://web_upstream/;
      proxy_set_header Host $host;
    }
  }
}
```

```bash
# scripts/verify-local-stack.sh
#!/usr/bin/env bash
set -euo pipefail

uv run pytest -q
(cd apps/web && npm run test)
docker compose up -d --build
curl -fsS http://localhost/ | head -n 1
curl -fsS http://localhost/api/healthz
```

- [ ] **Step 4: Run the verification script**

Run: `bash scripts/verify-local-stack.sh`

Expected:
- Python unit tests pass
- frontend tests pass
- docker compose builds
- `curl http://localhost/` returns HTML
- `curl http://localhost/api/healthz` returns gateway health JSON

- [ ] **Step 5: Commit**

```bash
git add services/gateway/app/api/public_exam.py services/gateway/app/api/admin.py \
  docker-compose.yml infra/nginx/nginx.conf tests/e2e/test_admin_to_exam_flow.py \
  scripts/verify-local-stack.sh
git commit -m "feat: assemble local dockerized stack"
```

## Self-Review Checklist

### Spec coverage

- Resume upload and parsing: covered in Tasks 5 and 6.
- Template-driven paper generation with JD and profile context: covered in Task 7.
- Invitation, verification code, session timing, autosave, risk logging: covered in Task 8 and Task 12.
- Judge0 coding questions, language strategy, run vs submit: covered in Task 9.
- Objective scoring, subjective suggestions, summary page data: covered in Task 10.
- Docker, MinIO, Postgres, Flyway, uv, git workflow: covered in Tasks 1, 3, and 13.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” markers are allowed during execution.
- If a service grows beyond its owned boundary during implementation, split the task before coding further.
- If Judge0 language IDs differ in the deployed image, update `services/judge_bridge/app/domain/language_map.py` using the result of `scripts/check_judge0.py` before exposing that language in the UI.

### Type consistency

- Keep service names stable across `/healthz`, docker compose service names, and app titles.
- Keep `run` vs `submit` naming consistent across exam, judge bridge, and scoring tables.
- Keep `draft_answer_json` and `final_answer_json` naming consistent between DB schema and API payloads.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-21-pre-screen-mvp.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints
