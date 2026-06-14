# SmartInv — developer shortcuts.
# The local stack (Postgres, Redis, SeaweedFS) is defined in docker-compose.yml.

.PHONY: dev-up dev-down dev-restart dev-logs bootstrap-buckets check-infra migrate migrate-down seed token

# Boot the local infrastructure and ensure the object-store bucket exists.
dev-up:
	docker compose up -d
	uv run python scripts/bootstrap_buckets.py

# Stop the local infrastructure (keeps volumes/data).
dev-down:
	docker compose down

# Restart the local infrastructure from scratch (keeps volumes/data).
dev-restart: dev-down dev-up

# Tail logs from all services.
dev-logs:
	docker compose logs -f

# Create the configured object-store bucket if missing (idempotent).
bootstrap-buckets:
	uv run python scripts/bootstrap_buckets.py

# Verify the API can reach Postgres, Redis, and the object store.
check-infra:
	uv run python scripts/check_infra.py

# Apply all database migrations.
migrate:
	uv run alembic -c services/api/alembic.ini upgrade head

# Roll back the most recent migration.
migrate-down:
	uv run alembic -c services/api/alembic.ini downgrade -1

# Seed local-dev fixture data (one tenant + admin user).
seed:
	uv run python scripts/seed_dev.py

# Mint a dev JWT.  Usage: make token TENANT=smartinv-dev ROLES=admin,planner
TENANT ?= smartinv-dev
ROLES ?= admin
token:
	uv run python scripts/dev_token.py --tenant $(TENANT) --roles $(ROLES)
