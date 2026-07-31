#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# 1) 先起数据依赖（postgres 就绪后 gateway 才能安全启动）
compose up -d --build postgres redis minio minio-init

echo "等待 postgres 就绪..."
deadline=$((SECONDS + 120))
postgres_container="$(compose ps -q postgres 2>/dev/null || true)"
until [[ -n "$postgres_container" ]] \
  && [[ "$(docker inspect --format '{{.State.Health.Status}}' "$postgres_container" 2>/dev/null)" == "healthy" ]]; do
  if (( SECONDS >= deadline )); then
    echo "postgres 未在 120s 内就绪，请检查容器日志" >&2
    compose ps
    exit 1
  fi
  sleep 2
  postgres_container="$(compose ps -q postgres 2>/dev/null || true)"
done
echo "postgres 已就绪"

# 2) 数据库迁移（SQL 均幂等，可重复执行；host 失败自动回退 docker flyway）
bash scripts/flyway-migrate.sh

# 3) 再起应用服务
compose up -d --build gateway web nginx
compose ps
