.PHONY: up down logs api web sdk-test example-worker lint format release-dry packages-build prod-up

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

packages-build:
	python -m pip install --upgrade build
	python -m build packages/sdk-python -o dist
	python -m build packages/cli -o dist
	ls -la dist

release-dry:
	python scripts/extract_changelog.py 0.1.0
	python scripts/bump_version.py 0.1.0

prod-up:
	docker compose -f docker-compose.prod.yml --env-file .env up -d
