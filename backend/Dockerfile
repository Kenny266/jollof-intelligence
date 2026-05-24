FROM python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a virtualenv so all packages are isolated and reproducible
RUN python -m venv /opt/venv

# Put the venv on PATH so every subsequent RUN and CMD uses it automatically
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies into the venv (layer-cached before code copy).
# Eval dependencies (bert-score, deepeval, datasets, …) live in
# requirements-eval.txt and are intentionally excluded from the API image
# to avoid the 500 MB+ torch download at build time.
COPY requirements.txt requirements-eval.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories (volumes will overlay these at runtime)
RUN mkdir -p data/raw data/processed data/chroma_db data/eval/reports
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
