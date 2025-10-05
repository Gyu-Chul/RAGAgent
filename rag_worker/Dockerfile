# RAG Worker Service Dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN uv sync --no-dev

# Production stage
FROM python:3.11-slim

# Install runtime dependencies (git for cloning repositories)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy only rag_worker-related files
COPY rag_worker/ ./rag_worker/
COPY pyproject.toml .
COPY README.md .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Health check for Celery worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import celery; from rag_worker.celery_app import app; print('Worker running') if app.control.inspect().active() else exit(1)" || exit 1

# Run RAG worker service
CMD ["python", "-m", "celery", "-A", "rag_worker.celery_app", "worker", "--loglevel=info"]