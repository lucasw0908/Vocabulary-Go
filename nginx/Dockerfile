FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/

RUN if [ -f ssl.csr ] && [ -f ssl.key ]; then \
        cp ssl.csr /etc/nginx/ssl.csr && \
        cp ssl.key /etc/nginx/ssl.key; \
    else \
        echo "SSL files not found, skipping copy"; \
    fi