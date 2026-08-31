# Makefile for sangre-signal-web

.PHONY: help build run dev stop clean logs status test image image-nginx \
	quadlet-install quadlet-validate quadlet-start quadlet-stop \
	quadlet-status quadlet-logs quadlet-uninstall verify

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
	@echo ""
	@echo "Podman / systemd hosts — use these, NOT the compose targets above:"
	@echo "  image             - Build the app image (no source needed on the target)"
	@echo "  quadlet-install   - Install the units and validate them"
	@echo "  quadlet-validate  - Parse units with the quadlet generator (no deploy)"
	@echo "  quadlet-start     - Start via systemd --user"
	@echo "  quadlet-stop      - Stop the units"
	@echo "  quadlet-status    - Unit state AND running containers"
	@echo "  quadlet-logs      - journalctl for the units"
	@echo "  quadlet-uninstall - Remove the units"
	@echo "  verify            - Assert the service is actually RUNNING, not just installed"

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
# ─────────────────────────────────────────────────────────────────────────────
# Quadlet deployment (podman + systemd)
#
# The compose targets above target a DOCKER host. On a podman host compose
# produces loose containers that systemd does not supervise: nothing restarts
# them, nothing orders them against the network, and `systemctl` reports
# nothing.
#
# The units carry NO host paths. The image is built here (or in CI) and the
# deployment only references it by tag; state lives in a named volume. An
# earlier version bind-mounted a source checkout into the target and built
# there, which is what produced the 9p failures: overlayfs cannot back onto 9p,
# a 9p mount is readable by exactly one uid, and it is not mounted when units
# first start at boot. A container deployment should not reach into the host.
# ─────────────────────────────────────────────────────────────────────────────

QUADLET_DIR ?= $(HOME)/.config/containers/systemd
QUADLET_GEN ?= /usr/libexec/podman/quadlet
IMAGE       ?= localhost/sangre-signal-web:latest
NGINX_IMAGE ?= localhost/sangre-signal-nginx:latest
UNITS       := sangre-signal-data.volume sangre-signal-web.container sangre-signal-nginx.container

image:
	podman build --tag $(IMAGE) --file Dockerfile .

image-nginx:
	podman build --tag $(NGINX_IMAGE) --file Containerfile.nginx .

quadlet-validate:
	@command -v podman >/dev/null || { echo "podman not found — this is a docker host, use the compose targets"; exit 1; }
	@test -x $(QUADLET_GEN) || { echo "quadlet generator missing at $(QUADLET_GEN)"; exit 1; }
	@out=$$($(QUADLET_GEN) -dryrun -user 2>&1); \
	  echo "$$out" | grep -iE "error|invalid|unsupported" && { echo "VALIDATION FAILED"; exit 1; } || true; \
	  for u in $(UNITS); do echo "$$out" | grep -q "$$u" || { echo "missing from generator output: $$u"; exit 1; }; done
	@echo "OK — all units parse"

quadlet-install:
	@command -v podman >/dev/null || { echo "podman not found"; exit 1; }
	@mkdir -p $(QUADLET_DIR)
	install -m 0644 $(addprefix quadlet/,$(UNITS)) $(QUADLET_DIR)/
	@systemctl --user daemon-reload
	@$(MAKE) --no-print-directory quadlet-validate
	@echo "Installed. Units are FILES now — they are not running."
	@echo "Run 'make quadlet-start' then 'make verify'."

quadlet-start:
	systemctl --user start sangre-signal-web.service
	@echo "nginx is the production profile and is opt-in:"
	@echo "  systemctl --user enable --now sangre-signal-nginx.service"

quadlet-stop:
	-systemctl --user stop sangre-signal-nginx.service
	systemctl --user stop sangre-signal-web.service

quadlet-status:
	@echo "── unit state ──"
	@systemctl --user --no-pager status sangre-signal-web.service 2>&1 | head -6 || true
	@echo "── containers ACTUALLY running ──"
	@podman ps --filter name=sangre-signal --format '{{.Names}}\t{{.Status}}' || true

quadlet-logs:
	journalctl --user -u sangre-signal-web.service -f

quadlet-uninstall: quadlet-stop
	rm -f $(addprefix $(QUADLET_DIR)/,$(UNITS))
	systemctl --user daemon-reload

# A unit file existing is not a service running. Fails unless the container is
# up AND answering. Do not report a deploy without it.
verify:
	@echo "── is a container running? ──"
	@podman ps --filter name=sangre-signal-web --format '{{.Names}} {{.Status}}' | grep -q . \
	  || { echo "FAIL: no running sangre-signal-web container"; exit 1; }
	@echo "── does it answer? ──"
	@curl -fsS http://localhost:5000/status >/dev/null \
	  || { echo "FAIL: container up but /status did not respond"; exit 1; }
	@echo "PASS: running and responding"
