# ==============================================================================
# Stage 1: Build Vue frontend with Bun
# ==============================================================================
FROM oven/bun:1 AS frontend-builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source files
COPY index.html ./
COPY vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY src/ ./src/

# Build the frontend
RUN bun run build

# ==============================================================================
# Stage 2: Python backend with static files
# ==============================================================================
FROM python:3.12-slim

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy Python project files
COPY pyproject.toml uv.lock ./

# Install Python dependencies (production only, no dev deps)
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dist ./dist

# Set Python path so wedplan module is importable
ENV PYTHONPATH=/app/backend

# Railway injects PORT, default to 8000 for local testing
ENV PORT=8000

# Expose the port (documentation only, Railway handles this)
EXPOSE ${PORT}

# Run uvicorn with dynamic port from environment
CMD ["sh", "-c", "uv run uvicorn wedplan.api.main:app --host 0.0.0.0 --port ${PORT}"]
