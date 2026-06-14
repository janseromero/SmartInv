-- SmartInv — Postgres extension bootstrap (CV1.E4, ADR-004).
--
-- Runs once on first container start (empty data directory) via the
-- docker-entrypoint-initdb.d hook. Enables the extensions the MVP data
-- platform depends on. `tsvector` is part of core PostgreSQL and needs no
-- extension. Table/schema creation belongs to CV1.E5 (Alembic), not here.

CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector: embeddings / RAG
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- trigram similarity / fuzzy search
