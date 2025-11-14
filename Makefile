COMPOSE_PROFILES ?= dev
IMAGE            ?= course-app:local
SERVICE          ?= app
CONTAINER_NAME   ?= course-app
HEALTH_URL       ?= http://127.0.0.1:8000/health

.PHONY: help build up down restart logs ps test lint-docker scan shell curl stop rm

help:
	@echo "Targets:"
	@echo "  build         - docker compose build ($(SERVICE), profile=$(COMPOSE_PROFILES))"
	@echo "  up            - docker compose up -d ($(SERVICE), profile=$(COMPOSE_PROFILES))"
	@echo "  down          - docker compose down"
	@echo "  restart       - down & up"
	@echo "  logs          - follow logs for $(SERVICE)"
	@echo "  ps            - docker compose ps"
	@echo "  test          - run scripts/test_container.sh (non-root, healthy, /health OK)"
	@echo "  lint-docker   - hadolint Dockerfile (does not fail build)"
	@echo "  scan          - trivy scan $(IMAGE) (HIGH,CRITICAL; does not fail build)"
	@echo "  shell         - interactive shell into container $(CONTAINER_NAME)"
	@echo "  curl          - curl $(HEALTH_URL)"
	@echo "  stop          - docker compose stop $(SERVICE)"
	@echo "  rm            - docker compose rm -f $(SERVICE)"

build:
	docker compose --profile $(COMPOSE_PROFILES) build $(SERVICE)

up:
	docker compose --profile $(COMPOSE_PROFILES) up -d $(SERVICE)

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f $(SERVICE)

ps:
	docker compose ps

test:
	scripts/test_container.sh

lint-docker:
	hadolint Dockerfile || true

scan: build
	trivy image --severity HIGH,CRITICAL --no-progress $(IMAGE) || true

shell:
	@CID=$$(docker ps --filter "name=^/$(CONTAINER_NAME)$$" --format '{{.ID}}'); \
	if [ -z "$$CID" ]; then CID=$$(docker compose ps -q $(SERVICE)); fi; \
	if [ -z "$$CID" ]; then echo "No running container for $(SERVICE)"; exit 1; fi; \
	docker exec -it $$CID /bin/sh

curl:
	curl -i $(HEALTH_URL)

stop:
	docker compose stop $(SERVICE)

rm:
	docker compose rm -f $(SERVICE)
