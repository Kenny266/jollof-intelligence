FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY task_a/ ./task_a/
COPY data/ ./data/

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "task_a.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
