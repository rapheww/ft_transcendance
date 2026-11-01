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

setup: check-podman check-npm
	@echo "Setting up Transcendence..."
	$(MAKE) install
	$(MAKE) db
	$(MAKE) migrate
	$(MAKE) seed-bots
	$(MAKE) simulate-bots > bot_simulation.log 2>&1 &
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
	@echo "  make check-podman    Check that Podman is installed"
	@echo "  make check-npm       Check that npm is installed"
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

check-podman:
	@command -v podman >/dev/null 2>&1 || { echo "ERROR: Podman is required. Install Podman and ensure it is available in PATH." >&2; exit 1; }

check-npm:
	@command -v npm >/dev/null 2>&1 || { echo "ERROR: npm is required. Install Node.js (which includes npm) and ensure it is available in PATH." >&2; exit 1; }

install: install-backend install-frontend
	@echo "Installation complete."

install-backend:
	@echo "Installing backend dependencies..."
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
	fi
	$(VENV_PIP) install -r backend/requirements.txt

install-frontend: check-npm
	@echo "Installing frontend dependencies..."
	cd frontend && rm -rf bin && mkdir bin && npm install
	@cd frontend/bin && echo "go to bin folder" && curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared && chmod +x cloudflared

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db: check-podman
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
	@echo "Ensuring test database exists..."
	@exists=$$(podman exec $(DB_CONTAINER) psql \
		-U transcendence \
		-d transcendence \
		-v ON_ERROR_STOP=1 \
		-tA \
		-c "SELECT EXISTS (SELECT FROM pg_database WHERE datname = 'transcendence_test')") || { echo "ERROR: Could not check for the test database." >&2; exit 1; }; \
	if [ "$$exists" = "t" ]; then \
		echo "Test database already exists."; \
	elif [ "$$exists" = "f" ]; then \
		podman exec $(DB_CONTAINER) createdb -U transcendence transcendence_test; \
	else \
		echo "ERROR: Unexpected response while checking for the test database." >&2; \
		exit 1; \
	fi
	@echo "Test database is ready!"

db-stop: check-podman
	@podman stop $(DB_CONTAINER) 2>/dev/null || true

db-status: check-podman
	@podman ps -a --filter name=$(DB_CONTAINER)

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------

migrate:
	$(VENV_PYTHON) -m alembic -c backend/alembic.ini upgrade head

# ---------------------------------------------------------------------------
# Bots generation
# ---------------------------------------------------------------------------

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

frontend: check-npm
	cd frontend && npm run dev

dev: check-npm
	@echo "Starting backend and frontend..."
	@trap 'trap - INT TERM EXIT; kill $$(jobs -p) 2>/dev/null; wait' INT TERM EXIT; \
		$(VENV_PYTHON) -m uvicorn backend.app.main:app --reload & \
		(cd frontend && npm run dev) & \
		(cd frontend/bin && ./cloudflared tunnel --url http://localhost:5173 2>&1 | while IFS= read -r line; do \
			url=$$(printf '%s\n' "$$line" | grep -oE 'https://[[:alnum:]-]+\.trycloudflare\.com' || true); \
			if [ -n "$$url" ]; then tunnel_url="$$url"; fi; \
			case "$$line" in *" INF "*) ;; *) printf '%s\n' "$$line";; esac; \
			case "$$line" in *" precheck complete "*) \
				if [ -n "$$tunnel_url" ]; then \
					printf '\n========================================\n'; \
					printf '  Cloudflare tunnel URL: %s\n' "$$tunnel_url"; \
					printf '========================================\n\n'; \
				fi;; \
			esac; \
		done) & \
		wait

# ---------------------------------------------------------------------------
# Tests / quality
# ---------------------------------------------------------------------------

test:
	$(VENV_PYTHON) -m pytest backend/tests

lint: check-npm
	cd frontend && npm run lint

build: check-npm
	cd frontend && npm run build

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: check-podman
	@echo "Stopping background processes..."
	@pkill -f "[s]imulate_bot_games" 2>/dev/null || true
	@pkill -f "[u]vicorn backend.app.main" 2>/dev/null || true
	@echo "Stopping PostgreSQL..."
	@podman stop $(DB_CONTAINER) 2>/dev/null || true
	@echo "Removing build artifacts..."
	@rm -rf frontend/dist
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@rm -rf .pytest_cache
	@rm -f bot_simulation.log
	@echo "Clean complete."

fclean: clean
	@echo "Removing PostgreSQL container..."
	@podman rm -f $(DB_CONTAINER) 2>/dev/null || true
	@echo "Removing dependencies..."
	@rm -rf $(VENV)
	@rm -rf frontend/node_modules
	@rm -rf frontend/bin
	@echo "Full clean complete."


.PHONY: help setup check-podman check-npm install install-backend install-frontend db db-stop db-status migrate seed-bots simulate-bots prepare-bots backend frontend dev test lint build clean fclean
