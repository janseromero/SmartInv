# SmartInv — developer shortcuts.
# The local stack (Postgres, Redis, SeaweedFS) is defined in docker-compose.yml.

.PHONY: dev-up dev-down dev-restart dev-logs bootstrap-buckets check-infra migrate migrate-down seed token api sync-fixtures score dedup anomalies forecast optimize

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

# Run the API dev server (foreground, auto-reload) on http://localhost:8000.
api:
	uv run uvicorn api.main:app --reload --app-dir services/api/src --port 8000

# Ingest the synthetic fixture inventory dataset for the dev tenant (CV2.E1).
sync-fixtures:
	uv run python scripts/sync_fixtures.py

# Recompute inventory health scores for the dev tenant (CV2.E3).
score:
	uv run python scripts/score.py

# Recompute duplicate-detection candidates for the dev tenant (CV2.E4).
dedup:
	uv run python scripts/dedup.py

# Recompute anomaly detections for the dev tenant (CV2.E5).
anomalies:
	uv run python scripts/anomalies.py

# Recompute demand forecasts for the dev tenant (CV3.E1).
forecast:
	uv run python scripts/forecast.py

# Recompute inventory recommendations for the dev tenant (CV3.E2/E3).
optimize:
	uv run python scripts/optimize.py
