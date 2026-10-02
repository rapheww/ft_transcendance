# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

DB_CONTAINER := transcendence-db

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help:
	@echo ""
	@echo "Transcendence development commands:"
	@echo ""
	@echo "  make install          Install backend and frontend dependencies"
	@echo "  make db               Create/start PostgreSQL container"
	@echo "  make db-stop         Stop PostgreSQL container"
	@echo "  make db-status       Show PostgreSQL container status"
	@echo "  make migrate         Run database migrations"
	@echo ""
	@echo "  make backend         Start FastAPI backend"
	@echo "  make frontend        Start Vite frontend"
	@echo "  make dev             Start backend and frontend"
	@echo ""
	@echo "  make test            Run backend tests"
	@echo "  make lint            Run frontend linter"
	@echo "  make build           Build frontend"
	@echo ""

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

install: install-backend install-frontend
	@echo "Installation complete."

install-backend:
	@echo "Installing backend dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
	fi
	$(VENV_PIP) install -r backend/requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db:
	@if podman container exists $(DB_CONTAINER); then \
		echo "PostgreSQL container already exists."; \
		podman start $(DB_CONTAINER) 2>/dev/null || true; \
	else \
		echo "Creating PostgreSQL container..."; \
		podman run \
			--name $(DB_CONTAINER) \
			-e POSTGRES_USER=transcendence \
			-e POSTGRES_PASSWORD=transcendence_dev \
			-e POSTGRES_DB=transcendence \
			-p 5432:5432 \
			-d docker.io/library/postgres:17; \
	fi

db-stop:
	@podman stop $(DB_CONTAINER) 2>/dev/null || true

db-status:
	@podman ps -a --filter name=$(DB_CONTAINER)

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------

migrate:
	$(VENV_PYTHON) -m alembic -c backend/alembic.ini upgrade head

# ---------------------------------------------------------------------------
# Development servers
# ---------------------------------------------------------------------------

backend:
	$(VENV_PYTHON) -m uvicorn backend.app.main:app --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend..."
	@trap 'kill 0' INT TERM EXIT; \
		$(VENV_PYTHON) -m uvicorn backend.app.main:app --reload & \
		(cd frontend && npm run dev) & \
		wait

# ---------------------------------------------------------------------------
# Tests / quality
# ---------------------------------------------------------------------------

test:
	$(VENV_PYTHON) -m pytest backend/tests

lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build


.PHONY: help install install-backend install-frontend db db-stop db-status migrate backend frontend dev test lint build
