FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY apps/api/pyproject.toml apps/api/alembic.ini apps/api/README.md /app/
COPY apps/api/app /app/app
COPY apps/api/alembic /app/alembic
COPY content /content

# Install dependencies
RUN uv venv /app/.venv && uv pip install -e .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/content"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
