FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY apps /app/apps
COPY src /app/src
COPY eval /app/eval
COPY migrations /app/migrations
COPY policies /app/policies
COPY alembic.ini /app/alembic.ini
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8080
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
