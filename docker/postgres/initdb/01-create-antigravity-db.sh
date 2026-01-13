#!/usr/bin/env bash
set -euo pipefail

# The official postgres image only creates a single database via POSTGRES_DB.
# The plugin expects an additional database (default: antigravity), so we create it on first init.

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=owner="$POSTGRES_USER" <<'EOSQL'
SELECT format('CREATE DATABASE %I OWNER %I', 'antigravity', :'owner')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'antigravity')\gexec
EOSQL
