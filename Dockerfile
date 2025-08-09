# Multi-stage build for optimized production image with uv
FROM python:3.12-slim AS builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libc6-dev \
    curl \
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

# Create non-root user with specific UID/GID for security
RUN groupadd --gid 1001 astroloh && \
    useradd --uid 1001 --gid 1001 --create-home --shell /bin/bash astroloh

# Create application directory with proper permissions
WORKDIR /app
RUN chown -R astroloh:astroloh /app

# Switch to non-root user early for security
USER astroloh

# Copy application code with proper ownership
COPY --chown=astroloh:astroloh alembic.ini ./
COPY --chown=astroloh:astroloh migrations/ ./migrations/
COPY --chown=astroloh:astroloh app/ ./app/

# Create required directories
RUN mkdir -p /app/swisseph /app/logs /app/tmp && \
    chmod 755 /app/swisseph /app/logs /app/tmp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production-ready startup command with uv and uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]