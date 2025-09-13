FROM python:3.11-slim

WORKDIR /app

ADD . /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpcre3-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uwsgi

RUN uv sync

RUN npm install
RUN npm run build

CMD ["uwsgi", "--ini", "uwsgi.ini"]
