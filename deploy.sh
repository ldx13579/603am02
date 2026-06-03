#!/bin/bash
set -euo pipefail

COMPOSE="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Git Habits Analyzer - One-Click Production Deployment ==="
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Creating from template..."
    cp .env.example .env
    echo "Please edit .env with your production values, then re-run this script:"
    echo "  vim .env"
    exit 1
fi

# Validate critical env vars
source .env
if [ -z "${POSTGRES_PASSWORD:-}" ] || [ "$POSTGRES_PASSWORD" = "githabits_pass" ]; then
    echo "WARNING: POSTGRES_PASSWORD is not set or is using default value."
    echo "Please set a strong password in .env before deploying to production."
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

if [ -z "${API_KEYS:-}" ] || [ "$API_KEYS" = "changeme-secret-key" ]; then
    echo "WARNING: API_KEYS is not set or is using default value."
    echo "Please set secure API keys in .env before deploying to production."
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

echo "[1/6] Building Docker images..."
$COMPOSE build

echo ""
echo "[2/6] Starting database services..."
$COMPOSE up -d redis postgres

echo ""
echo "[3/6] Waiting for PostgreSQL to be ready..."
RETRIES=30
until $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-githabits}" >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        echo "ERROR: PostgreSQL failed to start within timeout."
        $COMPOSE logs postgres
        exit 1
    fi
    echo "  Waiting for PostgreSQL... ($RETRIES attempts remaining)"
    sleep 2
done
echo "  PostgreSQL is ready."

echo ""
echo "[4/6] Initializing database (creating tables & running migrations)..."
$COMPOSE run --rm fastapi python -c "
from app.database import init_db
print('  Creating database tables...')
init_db()
print('  Database initialization complete.')
"

echo ""
echo "[5/6] Starting all services..."
$COMPOSE up -d

echo ""
echo "[6/6] Verifying deployment health..."
RETRIES=20
API_HEALTHY=false
while [ $RETRIES -gt 0 ]; do
    HTTP_CODE=$($COMPOSE exec -T fastapi python -c "
import httpx
try:
    r = httpx.get('http://localhost:8000/api/health', timeout=5)
    print(r.status_code)
except:
    print(0)
" 2>/dev/null || echo "0")

    if [ "$HTTP_CODE" = "200" ]; then
        API_HEALTHY=true
        break
    fi
    RETRIES=$((RETRIES - 1))
    sleep 3
done

echo ""
if [ "$API_HEALTHY" = true ]; then
    echo "=== Deployment Successful ==="
else
    echo "=== WARNING: API health check not responding ==="
    echo "Services may still be starting. Check logs:"
    echo "  $COMPOSE logs -f fastapi"
fi

echo ""
$COMPOSE ps

echo ""
echo "=== Access Points ==="
echo ""
echo "  Web UI:   http://localhost"
echo "  API:      http://localhost/api/health"
echo "  API Docs: http://localhost/api/docs (if enabled)"
echo ""
echo "=== Useful Commands ==="
echo ""
echo "  View logs:       $COMPOSE logs -f"
echo "  View API logs:   $COMPOSE logs -f fastapi"
echo "  Stop:            $COMPOSE down"
echo "  Restart:         $COMPOSE restart"
echo "  DB backup:       $COMPOSE exec fastapi python -c \"from app.tasks.scan_tasks import backup_database; backup_database()\""
echo "  Re-init DB:      $COMPOSE run --rm fastapi python -c \"from app.database import init_db; init_db()\""
echo ""
