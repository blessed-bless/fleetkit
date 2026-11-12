FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY backend/pyproject.toml backend/README.md /app/
COPY backend/fleetkit_api /app/fleetkit_api
COPY backend/fleetkit_worker /app/fleetkit_worker

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["uvicorn", "fleetkit_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
