FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
COPY apps ./apps
COPY infra/nginx ./infra/nginx

CMD ["sh", "-c", "printf 'web image placeholder\\n'"]
