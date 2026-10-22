# syntax=docker/dockerfile:1
# Multi-stage build with uv: dependencies are resolved from uv.lock, the runtime image
# contains only the virtualenv and runs as an unprivileged user.

FROM python:3.13-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra prod --no-install-project
COPY alembic.ini ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra prod --no-editable

FROM python:3.13-slim-trixie AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app:app /data
WORKDIR /app
COPY --from=build --chown=app:app /app/.venv /app/.venv
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/healthz')"
CMD ["fastapi-starter", "serve", "--host", "0.0.0.0", "--port", "8000", "--migrate"]
