FROM python:3.12-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY backend/pyproject.toml backend/README.md ./
COPY backend/fleetkit_api ./fleetkit_api
COPY backend/fleetkit_worker ./fleetkit_worker
RUN pip install --upgrade pip && pip install --prefix=/install .

FROM python:3.12-slim

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=builder /install /usr/local
USER appuser
EXPOSE 8000
CMD ["uvicorn", "fleetkit_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
