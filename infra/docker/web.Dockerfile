FROM nginx:1.27-alpine

WORKDIR /app

COPY infra/nginx ./infra/nginx

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
