FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

COPY vocabulary_go.conf /etc/nginx/conf.d/

RUN mkdir -p /etc/nginx/ssl

RUN if [ -f ssl.crt ] && [ -f ssl.key ]; then \
        cp ssl.crt /etc/nginx/ssl/vocabulary_go.crt && \
        cp ssl.key /etc/nginx/ssl/vocabulary_go.key; \
    else \
        echo "SSL files not found, skipping copy"; \
    fi