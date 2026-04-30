# Makefile for Retail Demand Forecaster & Auto-Replenishment Agent
# Provides convenient commands for development, testing, and deployment

# --- Configuration ---
SHELL := /bin/bash
PYTHON := python3
UV := uv
PIP := pip3
PROJECT_ROOT := $(shell pwd)
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
REPORTS_DIR := reports

# Docker
DOCKER_COMPOSE := docker compose
DOCKER_COMPOSE_FILE := docker-compose.yml

# Kubernetes
K8S_DIR := k8s
K8S_NAMESPACE ?= retail-forecaster
K8S_CONTEXT ?= $(shell kubectl config current-context 2>/dev/null || echo "default")

# --- Colors ---
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_CYAN := \033[36m
COLOR_RED := \033[31m

# --- Phony Targets ---
.PHONY: all help install dev test lint format clean build docker-build docker-up docker-down docker-logs k8s-apply k8s-delete k8s-status deploy ci-report

# --- Default Target ---
all: help

# --- Help ---
help:
	@echo "$(COLOR_BOLD)Retail Demand Forecaster - Makefile$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_CYAN)Development:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make install$(COLOR_RESET)      Install dependencies with UV"
	@echo "  $(COLOR_GREEN)make dev$(COLOR_RESET)         Start development server"
	@echo "  $(COLOR_GREEN)make mock-api$(COLOR_RESET)    Start mock supplier API server"
	@echo "  $(COLOR_GREEN)make generate-data$(COLOR_RESET) Generate sample data"
	@echo ""
	@echo "$(COLOR_CYAN)Testing:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make test$(COLOR_RESET)         Run all tests"
	@echo "  $(COLOR_GREEN)make test-cov$(COLOR_RESET)     Run tests with coverage report"
	@echo "  $(COLOR_GREEN)make test-unit$(COLOR_RESET)    Run unit tests only"
	@echo "  $(COLOR_GREEN)make test-integration$(COLOR_RESET) Run integration tests only"
	@echo ""
	@echo "$(COLOR_CYAN)Code Quality:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make lint$(COLOR_RESET)         Run flake8 linting"
	@echo "  $(COLOR_GREEN)make format$(COLOR_RESET)       Format code with black"
	@echo "  $(COLOR_GREEN)make typecheck$(COLOR_RESET)    Run mypy type checking"
	@echo ""
	@echo "$(COLOR_CYAN)Docker:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make docker-build$(COLOR_RESET) Build Docker images"
	@echo "  $(COLOR_GREEN)make docker-up$(COLOR_RESET)    Start services with docker-compose"
	@echo "  $(COLOR_GREEN)make docker-down$(COLOR_RESET)  Stop and remove containers"
	@echo "  $(COLOR_GREEN)make docker-logs$(COLOR_RESET)  Show container logs"
	@echo "  $(COLOR_GREEN)make docker-shell$(COLOR_RESET) Open shell in app container"
	@echo ""
	@echo "$(COLOR_CYAN)Kubernetes:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make k8s-apply$(COLOR_RESET)    Deploy to Kubernetes"
	@echo "  $(COLOR_GREEN)make k8s-delete$(COLOR_RESET)   Remove from Kubernetes"
	@echo "  $(COLOR_GREEN)make k8s-status$(COLOR_RESET)   Check deployment status"
	@echo "  $(COLOR_GREEN)make k8s-logs$(COLOR_RESET)     Show pod logs"
	@echo ""
	@echo "$(COLOR_CYAN)Utility:$(COLOR_RESET)"
	@echo "  $(COLOR_GREEN)make clean$(COLOR_RESET)        Remove generated files"
	@echo "  $(COLOR_GREEN)make ci-report$(COLOR_RESET)    Generate CI test report"
	@echo "  $(COLOR_GREEN)make demo$(COLOR_RESET)          Run full demo (build + start)"
	@echo ""

# --- Installation ---
install:
	@echo "$(COLOR_BLUE)Installing dependencies with UV...$(COLOR_RESET)"
	$(UV) sync --all-extras
	@echo "$(COLOR_GREEN)✓ Dependencies installed$(COLOR_RESET)"

# --- Development ---
dev:
	@echo "$(COLOR_BLUE)Starting FastAPI development server...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Dashboard: http://localhost:8000$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)API Docs:  http://localhost:8000/docs$(COLOR_RESET)"
	uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

mock-api:
	@echo "$(COLOR_BLUE)Starting mock supplier API server...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Mock API: http://localhost:8001$(COLOR_RESET)"
	python scripts/mock_api_server.py

generate-data:
	@echo "$(COLOR_BLUE)Generating sample data...$(COLOR_RESET)"
	$(PYTHON) scripts/generate_sample_data.py
	@echo "$(COLOR_GREEN)✓ Sample data generated$(COLOR_RESET)"

# --- Testing ---
test:
	@echo "$(COLOR_BLUE)Running all tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --tb=short
	@echo "$(COLOR_GREEN)✓ All tests passed$(COLOR_RESET)"

test-cov:
	@echo "$(COLOR_BLUE)Running tests with coverage...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --tb=short --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html:htmlcov
	@echo "$(COLOR_GREEN)✓ Coverage report generated: htmlcov/index.html$(COLOR_RESET)"

test-unit:
	@echo "$(COLOR_BLUE)Running unit tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TEST_DIR) -v -k "not test_api" --tb=short

test-integration:
	@echo "$(COLOR_BLUE)Running integration tests...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TEST_DIR) -v -k "test_api" --tb=short

# --- Code Quality ---
lint:
	@echo "$(COLOR_BLUE)Running flake8 linting...$(COLOR_RESET)"
	flake8 $(SRC_DIR) $(TEST_DIR) --max-line-length=100 --exclude=__pycache__,.venv,venv
	@echo "$(COLOR_GREEN)✓ Linting passed$(COLOR_RESET)"

format:
	@echo "$(COLOR_BLUE)Formatting code with black...$(COLOR_RESET)"
	black $(SRC_DIR) $(TEST_DIR) --line-length 100
	@echo "$(COLOR_GREEN)✓ Code formatted$(COLOR_RESET)"

typecheck:
	@echo "$(COLOR_BLUE)Running mypy type checking...$(COLOR_RESET)"
	mypy $(SRC_DIR) --ignore-missing-imports
	@echo "$(COLOR_GREEN)✓ Type checking passed$(COLOR_RESET)"

# --- Docker ---
docker-build:
	@echo "$(COLOR_BLUE)Building Docker images...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build
	@echo "$(COLOR_GREEN)✓ Docker images built$(COLOR_RESET)"

docker-up: docker-build
	@echo "$(COLOR_BLUE)Starting Docker containers...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "$(COLOR_YELLOW)Waiting for services to be ready...$(COLOR_RESET)"
	sleep 5
	@echo "$(COLOR_GREEN)✓ Services started$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Dashboard: http://localhost:8000$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Mock API:  http://localhost:8001$(COLOR_RESET)"

docker-down:
	@echo "$(COLOR_BLUE)Stopping Docker containers...$(COLOR_RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down
	@echo "$(COLOR_GREEN)✓ Containers stopped$(COLOR_RESET)"

docker-logs:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f

docker-shell:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec app /bin/bash

# --- Kubernetes ---
k8s-apply: k8s-build-configs
	@echo "$(COLOR_BLUE)Deploying to Kubernetes...$(COLOR_RESET)"
	kubectl config use-context $(K8S_CONTEXT)
	kubectl create namespace $(K8S_NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f $(K8S_DIR)/ -n $(K8S_NAMESPACE)
	@echo "$(COLOR_GREEN)✓ Deployed to Kubernetes namespace: $(K8S_NAMESPACE)$(COLOR_RESET)"

k8s-delete:
	@echo "$(COLOR_BLUE)Removing from Kubernetes...$(COLOR_RESET)"
	kubectl delete -f $(K8S_DIR)/ -n $(K8S_NAMESPACE) --ignore-not-found
	kubectl delete namespace $(K8S_NAMESPACE) --ignore-not-found
	@echo "$(COLOR_GREEN)✓ Removed from Kubernetes$(COLOR_RESET)"

k8s-status:
	@echo "$(COLOR_BLUE)Kubernetes deployment status:$(COLOR_RESET)"
	kubectl get all,configmap,secret -n $(K8S_NAMESPACE)
	kubectl get events -n $(K8S_NAMESPACE) --sort-by='.lastTimestamp'

k8s-logs:
	kubectl logs -n $(K8S_NAMESPACE) -l app=retail-forecaster -f --tail=50

k8s-build-configs:
	@echo "$(COLOR_BLUE)Generating Kubernetes configs...$(COLOR_RESET)"
	@mkdir -p $(K8S_DIR)
	@echo "$(COLOR_GREEN)✓ Kubernetes configs ready in $(K8S_DIR)/$(COLOR_RESET)"

# --- Utility ---
clean:
	@echo "$(COLOR_BLUE)Cleaning generated files...$(COLOR_RESET)"
	rm -rf $(REPORTS_DIR)/*.pdf $(REPORTS_DIR)/*.md
	rm -rf htmlcov .coverage .pytest_cache .mypy_cache
	@echo "$(COLOR_GREEN)✓ Cleaned generated files$(COLOR_RESET)"

ci-report:
	@echo "$(COLOR_BLUE)Generating CI test report...$(COLOR_RESET)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --tb=short --junitxml=test-results.xml
	@echo "$(COLOR_GREEN)✓ Test report generated: test-results.xml$(COLOR_RESET)"

demo: docker-build docker-up
	@echo "$(COLOR_GREEN)========================================$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)  Demo is running!$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)  Dashboard: http://localhost:8000$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)  API Docs:  http://localhost:8000/docs$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)  Mock API:  http://localhost:8001$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)========================================$(COLOR_RESET)"
