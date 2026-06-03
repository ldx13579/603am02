#!/bin/bash
set -euo pipefail

echo "=== Git Habits Analyzer - Production Deployment ==="
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and configure before deploying:"
    echo "  cp .env.example .env"
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

echo "[1/4] Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo ""
echo "[2/4] Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo ""
echo "[3/4] Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "[4/4] Checking service status..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Services:"
echo "  Web UI:   http://localhost"
echo "  API:      http://localhost/api/health"
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "  Stop:          docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "  Restart:       docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo ""
