FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/packages/backend-common/src:/app \
    PATH=/app/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir "uv>=0.8.15"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY packages/backend-common/src ./packages/backend-common/src
COPY services ./services

EXPOSE 8000

CMD ["uvicorn", "services.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
