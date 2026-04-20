FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
