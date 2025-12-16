.PHONY: help venv install run import-wikidata up down docker-run seed test lint format clean logs

TAG ?= graph-api:dev

help:
	@echo "Commands:"
	@echo "  make venv           Create local virtualenv (.venv)"
	@echo "  make install        Install requirements into .venv"
	@echo "  run         		 Run API locally"
	@echo "  import-wikidata     Import Wikidata entities"
	@echo "  docker-run  		 Build & run with docker-compose"
	@echo "  up/down     		 Start/stop containers"
	@echo "  seed        		 Seed Neo4j"
	@echo "  test        		 Run pytest"
	@echo "	 make lint        	 Run pylint with score >= 9.5"
	@echo "  format      		 Run black"
	@echo "  clean       		 Clean cache/pyc"
	@echo "  make tree           Show project tree (depth 3)"

venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		. .venv/bin/activate && pip install --upgrade pip; \
		echo "Created .venv"; \
	else echo ".venv already exists"; fi
	@echo "To activate: source .venv/bin/activate"

install: venv
	@. .venv/bin/activate && pip install -r requirements.txt

docker-run: up
up:
	docker-compose up --build -d

import-wikidata: wait-neo4j
	docker compose exec api python scripts/import_wikidata.py

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

wait-neo4j:
	@echo "Waiting for Neo4j HTTP interface..."
	@until curl -sf http://localhost:7474 >/dev/null; do \
		sleep 2; \
		echo "  ... waiting for Neo4j"; \
	done
	@echo "Neo4j is ready ✅"

docker-build:
	docker build -t $(TAG) .

down:
	docker-compose down

logs:
	docker-compose logs -f

seed: wait-neo4j
	docker-compose exec api python scripts/seed_data.py

test:
	docker-compose exec api pytest --cov=app --cov-report=term-missing --cov-report=html

lint:
	docker-compose exec api pylint app --fail-under=9.5

format:
	docker-compose exec api black .

clean:
	rm -rf .pytest_cache .mypy_cache .coverage **/__pycache__

tree:
	@if command -v tree >/dev/null 2>&1; then \
		tree -L 3 -I "node_modules|dist|.git|.venv|__pycache__"; \
	else \
		find . -maxdepth 3 -type d -not -path '*/\.*' | sort; \
	fi