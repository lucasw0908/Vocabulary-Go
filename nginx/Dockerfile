FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

COPY vocabulary_go.conf /etc/nginx/conf.d/

RUN mkdir -p /etc/nginx/ssl

COPY ssl/ssl.crt /etc/nginx/ssl/vocabulary_go.crt
COPY ssl/ssl.key /etc/nginx/ssl/vocabulary_go.key