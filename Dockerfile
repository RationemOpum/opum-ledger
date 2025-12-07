# Build stage
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim as builder

# Set working directory
WORKDIR /build

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./uv.lock

# Install dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

# Runtime stage
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/build/.venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder /build/.venv /build/.venv

# Copy application code
COPY tmw_ledger/ ./tmw_ledger/
COPY run_server.py ./

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /build/.venv
USER appuser

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /build/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

# Run the application using the venv's uvicorn
CMD ["/build/.venv/bin/uvicorn", "tmw_ledger.app:app", "--host", "0.0.0.0", "--port", "8000"]
