# ==============================================================================
# Native Environment Configuration
# ==============================================================================
# These variables are used for running the application directly on the host machine.
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
UV := uv

# ==============================================================================
# Docker Compose command detection
# ==============================================================================
# Check if 'docker-compose' (v1) is available
ifneq (,$(shell command -v docker-compose 2>/dev/null))
    DOCKER_COMPOSE := docker-compose
else
    # Fallback to 'docker compose' (v2)
    DOCKER_COMPOSE := docker compose
endif

# ==============================================================================
# Phony Targets
# ==============================================================================
# Use .PHONY to declare targets that are not actual files.
# This prevents conflicts with files of the same name and improves performance.
.PHONY: help init run migrate upgrade clean lint format check docker-build docker-up docker-down docker-logs

# ==============================================================================
# Help / Documentation
# ==============================================================================
# The default command when a developer runs `make` without any arguments.
# It serves as the main documentation for the project's commands.
help:
	@echo "------------------------------------------------------------------------"
	@echo " Spark Companion - Development Commands"
	@echo "------------------------------------------------------------------------"
	@echo "Usage: make [command]"
	@echo ""
	@echo "Native Development (runs on your machine):"
	@echo "  init           Initializes the local Python environment (creates venv, installs deps)."
	@echo "  run            Runs the FastAPI application locally with auto-reload."
	@echo "  upgrade        Applies all pending database migrations to the local database."
	@echo "  migrate        Generates a new migration script using the local environment."
	@echo "                 Usage: make migrate m=\"Your descriptive message\""
	@echo ""
	@echo "Docker Development (runs in containers):"
	@echo "  docker-build   Builds the Docker images for the application."
	@echo "  docker-up      Starts the application services (backend, db) in detached mode."
	@echo "  docker-down    Stops and removes the application's Docker containers."
	@echo "  docker-logs    Follows the logs of the backend service."
	@echo ""
	@echo "Code Quality & Formatting (runs locally):"
	@echo "  lint           Checks the entire project for linting errors with Ruff."
	@echo "  format         Formats all Python files using Black and Ruff Formatter."
	@echo "  check          Runs both the linter and formatter, automatically fixing issues."
	@echo ""
	@echo "Housekeeping:"
	@echo "  clean          Removes the local virtual environment and all __pycache__ directories."
	@echo "------------------------------------------------------------------------"

# ==============================================================================
# Native Development Commands (UNCHANGED)
# ==============================================================================
check_uv:
	@if ! command -v $(UV) &> /dev/null; then \
		echo "ERROR: 'uv' is not installed or not in your PATH."; \
		echo "Please install it first. See: https://docs.astral.sh/uv/#installation"; \
		exit 1; \
	fi

# Setup the initial development environment using only uv.
init: check_uv
	@echo "--> Syncing dependencies into the environment with uv..."
	@$(UV) sync --locked
	@echo ""
	@echo "------------------------------------------------------------------------"
	@echo " ✅ Environment initialized successfully."
	@echo ""
	@echo " ⚠️  IMPORTANT: This native setup requires PostgreSQL and Redis."
	@echo "    Please ensure they are installed and running locally, or that your"
	@echo "    .env file is configured to point to remote database/cache servers."
	@echo ""
	@echo "    Next steps: Run 'make upgrade' to set up the DB, then 'make run'."
	@echo "------------------------------------------------------------------------"

run:
	@echo "--> Starting Spark Companion (http://127.0.0.1:8181)..."
	@$(VENV_DIR)/bin/uvicorn app.main:app --reload --port 8181

upgrade:
	@echo "--> Applying database migrations..."
	@set -a; source .env; set +a; \
	$(VENV_DIR)/bin/alembic upgrade head
	@echo "--> Migrations applied."

migrate:
	@if [ -z "$(m)" ]; then \
		echo "ERROR: Migration message is required."; \
		echo "Usage: make migrate m=\"your message\""; \
		exit 1; \
	fi
	@echo "--> Generating new migration: $(m)"
	@set -a; source .env; set +a; \
	$(VENV_DIR)/bin/alembic revision --autogenerate -m "$(m)"

# ==============================================================================
# Docker Development Commands
# ==============================================================================
docker-build:
	@echo "--> Building Docker images..."
	@$(DOCKER_COMPOSE) build

docker-up:
	@echo "--> Starting Docker services in detached mode..."
	@$(DOCKER_COMPOSE) up -d

docker-down:
	@echo "--> Stopping and removing Docker containers..."
	@$(DOCKER_COMPOSE) down

docker-logs:
	@echo "--> Following logs for the backend service..."
	@$(DOCKER_COMPOSE) logs -f backend

# ==============================================================================
# Code Quality & Formatting
# ==============================================================================
lint:
	@echo "--> Linting project with Ruff..."
	@$(VENV_DIR)/bin/ruff check .

format:
	@echo "--> Formatting code with Black and Ruff..."
	@$(VENV_DIR)/bin/black .
	@$(VENV_DIR)/bin/ruff format .

check:
	@echo "--> Checking and fixing code style..."
	@$(VENV_DIR)/bin/ruff check . --fix
	@$(VENV_DIR)/bin/black .
	@$(VENV_DIR)/bin/ruff format .
	@echo "--> Style check and fix complete."

# ==============================================================================
# Housekeeping
# ==============================================================================
clean:
	@echo "--> Cleaning up project..."
	@rm -rf $(VENV_DIR)
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@echo "--> Cleanup complete."
