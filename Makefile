PY?=python3

.PHONY: build up down clean test images

build:
	docker compose build

up: build
	docker compose up -d

down:
	docker compose down

clean: down
	docker system prune -f --volumes

images:
	docker images | grep blockchain || true

test:
	PYTHONPATH=$(pwd) $(PY) -m pytest -q tests/test_core.py

ci-build:
	docker compose build --pull

cleanup:
	./scripts/docker-cleanup.sh --yes
