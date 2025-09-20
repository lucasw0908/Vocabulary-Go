FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

COPY vocabulary_go.conf /etc/nginx/sites-enabled/

RUN if [ -f ssl/ssl.crt ] && [ -f ssl/ssl.key ]; then \
        cp ssl/ssl.crt /etc/nginx/ssl/vocabulary_go.crt && \
        cp ssl/ssl.key /etc/nginx/ssl/vocabulary_go.key; \
    else \
        echo "SSL files not found, skipping copy"; \
    fi