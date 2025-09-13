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

# Install Python packages
RUN pip install --no-cache-dir uwsgi

# Sync dependencies with uv
RUN uv sync

# Build frontend
RUN npm install
RUN npm run build

# Start the app
CMD ["uwsgi", "--ini", "uwsgi.ini"]