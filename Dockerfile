FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
# installs exactly the versions in uv.lock and skips dev tools like pytest.
# --frozen fails loudly if the lock file is stale
RUN uv sync --frozen --no-dev --no-install-project

# code the app needs to run, including migrations and the server. Tests and .env are not copied
COPY alembic.ini server.py ./
COPY migrations ./migrations
COPY task_tracker ./task_tracker

# Run as normal user, not root.
RUN useradd --system --uid 1000 app
USER app

EXPOSE 8000
CMD ["python", "server.py"]
