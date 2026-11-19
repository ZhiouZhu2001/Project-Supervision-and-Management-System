# Every documented command lives here. Nothing else should be run by hand.
#
# .RECIPEPREFIX keeps recipes free of literal tabs, which do not survive a
# round trip through editors and CI config on Windows. GNU Make >= 3.82.
.RECIPEPREFIX = >

COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml
PROD_COMPOSE := docker compose -f docker-compose.yml -f docker-compose.prod.yml

.DEFAULT_GOAL := help

.PHONY: help setup dev down logs ps build restart migrate migration test test-api test-web lint fmt psql shell-api health backup restore-drill nuke deploy ps-prod certs certs-standalone certs-renew restore logs-prod backup restore-drill

help:
> @echo "make dev          bring the stack up (build + start + health check)"
> @echo "make down         stop the stack"
> @echo "make logs         follow logs"
> @echo "make ps           show service state"
> @echo "make migrate      alembic upgrade head"
> @echo "make migration m= create a migration"
> @echo "make test         api tests + web typecheck"
> @echo "make test-api     pytest"
> @echo "make test-web     tsc --noEmit"
> @echo "make lint         ruff + tsc"
> @echo "make fmt          ruff format + prettier"
> @echo "make psql         psql into the database"
> @echo "make health       curl the health endpoint"
> @echo "make backup       run the backup sidecar once"
> @echo "make restore-drill restore the newest snapshot into a scratch database"
> @echo "make nuke         stop and delete volumes"
> @echo ""
> @echo "Production:"
> @echo "make deploy       build and start the production stack"
> @echo "make ps-prod      service state on the host"
> @echo "make logs-prod    follow host service logs"
> @echo "make certs        first Let's Encrypt certificate (webroot)"
> @echo "make certs-renew  dry-run the renewal"
> @echo "make restore f=   restore a backup snapshot (destructive)"

setup:
> @test -f .env || (cp .env.example .env && echo "created .env from .env.example — development defaults already work without it")

dev:
> $(COMPOSE) up -d --build
> @$(MAKE) --no-print-directory health

down:
> $(COMPOSE) down

logs:
> $(COMPOSE) logs -f --tail=100

ps:
> $(COMPOSE) ps

build:
> $(COMPOSE) build

restart:
> $(COMPOSE) restart

migrate:
> $(COMPOSE) exec api uv run --no-sync alembic upgrade head

migration:
> @test -n "$(m)" || (echo 'usage: make migration m="describe the change"' && exit 1)
> $(COMPOSE) exec api uv run --no-sync alembic revision --autogenerate -m "$(m)"

test: test-api test-web

test-api:
> $(COMPOSE) exec api uv run --no-sync pytest -q

test-web:
> $(COMPOSE) exec web pnpm lint

lint:
> $(COMPOSE) exec api uv run --no-sync ruff check app tests
> $(COMPOSE) exec web pnpm lint

fmt:
> $(COMPOSE) exec api uv run --no-sync ruff format app tests
> $(COMPOSE) exec web pnpm format

psql:
> $(COMPOSE) exec db psql -U $${POSTGRES_USER:-app} -d $${POSTGRES_DB:-supervision}

shell-api:
> $(COMPOSE) exec api /bin/sh

health:
> @curl -fsS http://localhost:8080/api/healthz && echo "" || (echo "health check failed — see make logs" && exit 1)

backup:
> docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup.sh

restore-drill:
> @echo "see docs/BACKUP.md: the drill needs a scratch database and two volumes"
> @echo "the exact procedure and its last result are recorded there"

nuke:
> $(COMPOSE) down -v

# --- Production ----------------------------------------------------------
# These wrap PROD_COMPOSE so no document has to spell out a compose
# invocation (AGENTS: everything runs through make).

deploy:
> $(PROD_COMPOSE) up -d --build
> $(PROD_COMPOSE) ps

ps-prod:
> $(PROD_COMPOSE) ps

logs-prod:
> $(PROD_COMPOSE) logs -f --tail=100

certs:
> $(PROD_COMPOSE) run --rm --entrypoint sh certbot -c \
>   'certbot certonly --webroot -w /var/www/certbot -d "$$DOMAIN" --email "$$APP_EMAIL" --agree-tos --no-eff-email'

certs-standalone:
> $(PROD_COMPOSE) run --rm -p 80:80 --entrypoint certbot certbot \
>   certonly --standalone -d "$$DOMAIN" --email "$$APP_EMAIL" --agree-tos --no-eff-email

certs-renew:
> $(PROD_COMPOSE) run --rm --entrypoint certbot certbot renew --dry-run

restore:
> @test -n "$(f)" || (echo 'usage: make restore f=<snapshot-id|latest>' && exit 1)
> $(PROD_COMPOSE) run --rm backup /usr/local/bin/restore.sh $(f)
