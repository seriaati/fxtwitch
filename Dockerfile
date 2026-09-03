# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies in their own layer so they are only rebuilt when the
# lockfile changes, not on every source edit.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


FROM python:3.11-slim-trixie

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# The app writes its SQLite response cache (cache.db) into the working
# directory, so /app must be owned by the runtime user.
COPY --from=builder --chown=nonroot:nonroot /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER nonroot
WORKDIR /app

EXPOSE 8010

CMD ["uvicorn", "fxtwitch.app:app", "--host", "0.0.0.0", "--port", "8010"]
