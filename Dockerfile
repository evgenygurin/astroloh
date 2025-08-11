# Multi-stage build for optimized production image with uv
FROM python:3.12-slim AS builder

# Install system dependencies for building Python packages including Swiss Ephemeris
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libc6-dev \
    curl \
    libsqlite3-dev \
    libswe-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory for build context
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
# Include README for project metadata and source package for editable install
COPY README.md ./
COPY app/ ./app/

# Install Python dependencies with uv (full dependencies for Linux)
RUN cd /app && uv venv && uv pip install -e ".[full,dev]"

# Production stage
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && rm -rf /tmp/*

# Install uv in production stage and copy virtual environment from builder stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder /app/.venv /opt/venv

# Create non-root user and group for security
RUN groupadd -r astroloh && useradd -r -g astroloh -s /bin/bash -m astroloh

# Create application directory
WORKDIR /app

# Copy application code
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY app/ ./app/

# Create required directories and set ownership
RUN mkdir -p /app/swisseph /app/logs /app/tmp && \
    chmod 755 /app/swisseph /app/logs /app/tmp && \
    chown -R astroloh:astroloh /app && \
    chown -R astroloh:astroloh /opt/venv

# Switch to non-root user
USER astroloh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production-ready startup command using python -m to avoid shebang issues
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]