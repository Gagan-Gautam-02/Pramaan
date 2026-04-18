.PHONY: help start stop build health test lint clean add-model retrain eval

# ──────────────────────────────────────────────
#  Variables
# ──────────────────────────────────────────────
NAME        ?= my_model
MEDIA_TYPE  ?= image
PORT        ?= 5010
OPTIMIZER   ?= none
TRIALS      ?= 50
SAMPLES     ?= 400

# ──────────────────────────────────────────────
#  Help
# ──────────────────────────────────────────────
help:
	@echo ""
	@echo "  Pramaan — Makefile Commands"
	@echo "  ───────────────────────────────────────────────"
	@echo "  make start                     Start all services (Docker Compose)"
	@echo "  make stop                      Stop all services"
	@echo "  make build                     Rebuild Docker images"
	@echo "  make health                    Check health of all services"
	@echo "  make test                      Run system tests"
	@echo "  make lint                      Run black + flake8"
	@echo "  make add-model                 Register a new model"
	@echo "    NAME=my_model MEDIA_TYPE=image PORT=5010"
	@echo "  make retrain                   Full retrain pipeline"
	@echo "    MEDIA_TYPE=image [OPTIMIZER=optuna] [TRIALS=100]"
	@echo "  make eval                      Re-train from cached features"
	@echo "    MEDIA_TYPE=image"
	@echo "  make clean                     Remove containers and caches"
	@echo ""

# ──────────────────────────────────────────────
#  Service lifecycle
# ──────────────────────────────────────────────
start:
	docker compose up -d --build
	@echo ""
	@echo "  ✅ Pramaan is running!"
	@echo "  Dashboard  → http://localhost:8888"
	@echo "  API Docs   → http://localhost:8000/docs"
	@echo ""

stop:
	docker compose down

build:
	docker compose build

# ──────────────────────────────────────────────
#  Health check
# ──────────────────────────────────────────────
health:
	@python scripts/health_check.py

# ──────────────────────────────────────────────
#  Tests & Linting
# ──────────────────────────────────────────────
test:
	@pip install pytest httpx -q
	@pytest tests/ -v

lint:
	@pip install black flake8 -q
	@black api/ models/ scripts/ sdk/ --check
	@flake8 api/ models/ scripts/ sdk/ --max-line-length=120 --extend-ignore=E501,W503

fmt:
	@black api/ models/ scripts/ sdk/

# ──────────────────────────────────────────────
#  Model management
# ──────────────────────────────────────────────
add-model:
	python scripts/add_model.py --name $(NAME) --media-type $(MEDIA_TYPE) --port $(PORT)

retrain:
	python scripts/retrain_pipeline.py \
		--media-type $(MEDIA_TYPE) \
		--optimizer $(OPTIMIZER) \
		--trials $(TRIALS) \
		--samples $(SAMPLES)

eval:
	python scripts/retrain_pipeline.py \
		--media-type $(MEDIA_TYPE) \
		--skip-inference

# ──────────────────────────────────────────────
#  Cleanup
# ──────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .retrain_cache/ api/pramaan.db
	@echo "✅ Cleaned up."
