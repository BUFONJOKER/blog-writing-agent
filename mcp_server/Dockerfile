# Multi-stage build for a slim image
FROM python:3.12-slim-bookworm AS builder
ENV UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.6.17 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Health check that works for both Stdio and SSE
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD pgrep -f "python server.py" || exit 1

# Start in SSE mode for cloud deployment
CMD ["python", "server.py", "--sse"]