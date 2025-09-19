FROM python:3.11-slim

WORKDIR /app

# Copy app and uv binary
ADD . /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    python3-dev \
    libpcre2-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv and uwsgi
RUN uv sync
RUN uv pip install --no-cache-dir uwsgi

# Build frontend
RUN npm install
RUN npm run build

# Compile translations
RUN uv run pybabel compile -d translations

# Start the app
CMD ["uv", "run", "uwsgi", "--ini", "uwsgi.ini"]