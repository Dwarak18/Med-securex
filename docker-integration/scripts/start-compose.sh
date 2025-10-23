#!/usr/bin/env bash
# Start the docker-compose stack for docker-integration
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$HERE/docker-compose.yml"

echo "Starting docker-compose from: $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" up -d --build
echo "Services started. Use 'docker compose -f $COMPOSE_FILE ps' to view status."
