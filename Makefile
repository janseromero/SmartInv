# SmartInv — developer shortcuts.
# The local stack (Postgres, Redis, SeaweedFS) is defined in docker-compose.yml.

.PHONY: dev-up dev-down dev-restart dev-logs bootstrap-buckets check-infra

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
