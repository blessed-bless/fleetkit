.PHONY: up down logs api web sdk-test example-worker lint format

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

api:
	cd backend && python -m uvicorn fleetkit_api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd frontend && npm run dev

sdk-test:
	cd packages/sdk-python && python -m pytest -q

example-worker:
	cd examples/http-worker && python worker.py

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

format:
	cd backend && ruff format .
