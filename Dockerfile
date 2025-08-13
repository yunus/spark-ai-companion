# Build stage - includes all build dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Enable bytecode compilation and copy mode for build
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first for better caching
COPY uv.lock pyproject.toml ./

# Install dependencies (this layer will be cached unless dependencies change)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy source code and install the project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Runtime stage - minimal image
FROM python:3.12-slim-bookworm as runtime

# Install only runtime audio dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

## Health check
#HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#    CMD python -c "import requests; requests.get('http://localhost:8181/health', timeout=5)" || exit 1

# Expose app port
EXPOSE 8181

# Reset the entrypoint
ENTRYPOINT []

# Set the container startup command
CMD ["/bin/bash", "./bin/entrypoint.sh"]
