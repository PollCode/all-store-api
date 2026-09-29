#!/bin/sh
set -e

echo "▶ Waiting for database to be ready..."
# Reintenta hasta 30 veces (docker-compose ya tiene depends_on con healthcheck,
# pero esto añade una red de seguridad)
ATTEMPTS=30
until python -c "import os, psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])" 2>/dev/null; do
    ATTEMPTS=$((ATTEMPTS - 1))
    if [ "$ATTEMPTS" -le 0 ]; then
        echo "✗ Database not reachable, giving up."
        exit 1
    fi
    sleep 1
done
echo "✓ Database is up."

echo "▶ Running Alembic migrations..."
alembic upgrade head

echo "▶ Starting application..."
exec "$@"