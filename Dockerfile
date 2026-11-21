# Hosted build (Render or any container host): one container serves the console and the MCP server on $PORT.
# Local development does not use this; see README (backend: uv run python -m app.main, frontend: npx vite).

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npx vite build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy SHIFTTRACE_SINGLE_PORT=1
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/
RUN cd backend && uv sync --frozen --no-dev --no-install-project
COPY backend/ backend/
COPY demo_data/ demo_data/
COPY experiments/ experiments/
COPY --from=web /web/dist frontend/dist
WORKDIR /app/backend
EXPOSE 10000
CMD ["uv", "run", "--no-sync", "python", "-m", "app.main"]
