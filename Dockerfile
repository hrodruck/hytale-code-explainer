FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Dependencies first (excellent caching)
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Security: non-root user (commented out because of cloud restrictions
# RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
# USER appuser

ENTRYPOINT ["uv", "run", "main.py"]