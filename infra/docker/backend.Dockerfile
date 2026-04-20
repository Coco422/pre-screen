FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "pydantic>=2.10.0" "pydantic-settings>=2.8.0"

COPY packages/backend-common/src ./packages/backend-common/src

ENV PYTHONPATH=/app/packages/backend-common/src

CMD ["python", "-c", "from pre_screen_common.settings import AppSettings; print('backend image ready')"]
