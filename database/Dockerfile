FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    datasets==2.19.1 \
    tqdm==4.66.4

COPY database/ ./database/
COPY data/ ./data/

ENV PYTHONPATH=/app

CMD ["python", "-m", "database.scripts.ingest"]
