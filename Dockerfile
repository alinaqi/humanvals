# Stage 1: build the React dashboard
FROM node:22-slim AS dashboard
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 2: Python runtime serving API + built dashboard
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --extra server --no-dev --no-group dev
COPY --from=dashboard /app/dashboard/dist ./dashboard/dist

ENV PATH="/app/.venv/bin:$PATH" \
    HUMANVALS_DB=/var/data/humanvals.db
EXPOSE 10000
CMD ["sh", "-c", "uvicorn humanvals.server.app:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}"]
