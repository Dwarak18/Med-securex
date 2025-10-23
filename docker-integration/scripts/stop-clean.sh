#!/usr/bin/env bash
# Stop docker-compose stack and remove containers, volumes and build cache
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$HERE/docker-compose.yml"

echo "Stopping docker-compose stack using: $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" down --volumes --remove-orphans

echo "Pruning unused Docker resources (images, build cache). You will be prompted for confirmation if not using --force."
docker system prune -af --volumes

echo "Done."
