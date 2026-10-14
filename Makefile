# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

DB_CONTAINER := transcendence-db

.DEFAULT_GOAL := setup

# ---------------------------------------------------------------------------
# Main development workflow
# ---------------------------------------------------------------------------

setup:
	@echo "Setting up Transcendence..."
	$(MAKE) install
	$(MAKE) db
	$(MAKE) migrate
	$(MAKE) dev

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help:
	@echo ""
	@echo "Transcendence development commands:"
	@echo ""
	@echo "  make setup           Install, start DB, migrate, and run the app"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make db              Create/start PostgreSQL container"
	@echo "  make db-stop         Stop PostgreSQL container"
	@echo "  make db-status       Show PostgreSQL container status"
	@echo "  make migrate         Run database migrations"
	@echo "  make seed-bots       Generate and insert 32 AI bots"
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
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		if podman exec $(DB_CONTAINER) pg_isready \
			-U transcendence \
			-d transcendence \
			-q; then \
			echo "PostgreSQL is ready!"; \
			exit 0; \
		fi; \
		echo "  PostgreSQL is not ready yet... ($$i/30)"; \
		sleep 1; \
	done; \
	echo "ERROR: PostgreSQL did not become ready."; \
	podman logs $(DB_CONTAINER); \
	exit 1

db-stop:
	@podman stop $(DB_CONTAINER) 2>/dev/null || true

db-status:
	@podman ps -a --filter name=$(DB_CONTAINER)

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------

migrate:
	$(VENV_PYTHON) -m alembic -c backend/alembic.ini upgrade head

seed-bots:
	$(VENV_PYTHON) -m backend.scripts.generate_bots

simulate-bots:
	$(VENV_PYTHON) -m backend.scripts.simulate_bot_games

prepare-bots: seed-bots simulate-bots

# ---------------------------------------------------------------------------
# Development servers
# ---------------------------------------------------------------------------

backend:
	$(VENV_PYTHON) -m uvicorn backend.app.main:app --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend..."
	@trap 'trap - INT TERM EXIT; kill $$(jobs -p) 2>/dev/null; wait' INT TERM EXIT; \
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

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean:
	@echo "Stopping PostgreSQL..."
	@podman stop $(DB_CONTAINER) 2>/dev/null || true
	@echo "Removing build artifacts..."
	@rm -rf frontend/dist
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@echo "Clean complete."

fclean: clean
	@echo "Removing PostgreSQL container..."
	@podman rm -f $(DB_CONTAINER) 2>/dev/null || true
	@echo "Removing dependencies..."
	@rm -rf $(VENV)
	@rm -rf frontend/node_modules
	@echo "Full clean complete."


.PHONY: help setup install install-backend install-frontend db db-stop db-status migrate seed-bots backend frontend dev test lint build clean fclean
