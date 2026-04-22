.PHONY: help test lint check-deploy dev stop clean

# Default target
help:
	@echo "Short Chain Commerce - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev       - Start API server in development mode"
	@echo "  make test      - Run all tests"
	@echo "  make lint      - Run linting checks"
	@echo "  make check     - Run deployment readiness checks"
	@echo ""
	@echo "Docker:"
	@echo "  make build     - Build Docker image"
	@echo "  make up        - Start all services (dev)"
	@echo "  make up-staging - Start staging environment"
	@echo "  make down      - Stop all services"
	@echo ""
	@echo "Database:"
	@echo "  make db-init   - Initialize database"
	@echo "  make db-reset  - Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make metrics   - Show API metrics"
	@echo "  make health    - Check service health"
	@echo ""

# Development
dev:
	python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Tests
test:
	python -m pytest tests/ -v --tb=short

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	python -m flake8 src/ --max-line-length=127
	python -m black --check src/ pipeline/ 2>/dev/null || echo "Skipping black"

check:
	python scripts/check_deploy.py

# Docker
build:
	docker build -t shortchain:latest .

up:
	docker-compose up -d

up-staging:
	docker-compose -f docker-compose.staging.yml up -d

down:
	docker-compose down

restart:
	docker-compose restart

# Database
db-init:
	python -m src.database.db_manager

db-reset:
	@echo "WARNING: This will delete all data!"
	rm -f data/*.db

# Monitoring
metrics:
	curl http://localhost:8000/api/v1/metrics

health:
	curl http://localhost:8000/health

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf data/*.db
	rm -rf logs/*.log
