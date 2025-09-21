FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY site.conf /etc/nginx/conf.d/

RUN mkdir -p /etc/nginx/ssl
COPY ssl/ssl.crt /etc/nginx/ssl/ssl.crt
COPY ssl/ssl.key /etc/nginx/ssl/ssl.key