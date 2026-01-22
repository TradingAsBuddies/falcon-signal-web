# Makefile for sangre-signal-web

.PHONY: help build run dev stop clean logs status test

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build Docker image"
	@echo "  run       - Run with Docker Compose"
	@echo "  dev       - Run in development mode"
	@echo "  stop      - Stop containers"
	@echo "  clean     - Clean up containers and images"
	@echo "  logs      - Show logs"
	@echo "  status    - Show container status"
	@echo "  test      - Run tests"
	@echo "  prod      - Run in production mode with nginx"

# Build Docker image
build:
	docker-compose build

# Run with Docker Compose
run:
	docker-compose up --build

# Run in background
run-bg:
	docker-compose up -d --build

# Development mode
dev:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Starting development server..."
	FLASK_ENV=development python run.py

# Production mode with nginx
prod:
	docker-compose --profile production up --build

# Stop containers
stop:
	docker-compose down

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Show logs
logs:
	docker-compose logs -f

# Show status
status:
	docker-compose ps

# Test the application
test:
	@echo "Running basic tests..."
	curl -f http://localhost:5000/status || echo "Service not running"

# Install dependencies locally
install:
	pip install -r requirements.txt

# Quick start
start: build run-bg
	@echo "Application started at http://localhost:5000"
	@echo "Use 'make logs' to see logs"
	@echo "Use 'make stop' to stop the application"