#!/usr/bin/env bash
set -euo pipefail

CONFIRM=no
if [[ "${1-}" == "--yes" ]]; then
  CONFIRM=yes
fi

echo "Listing stopped containers:" 
docker ps -a --filter "status=exited" --format "table {{.ID}}\t{{.Names}}\t{{.Size}}"

echo
echo "Listing dangling images:" 
docker images --filter dangling=true --format "table {{.ID}}\t{{.Repository}}:{{.Tag}}\t{{.Size}}"

if [[ "$CONFIRM" == "no" ]]; then
  read -p "Proceed to remove stopped containers and dangling images? [y/N] " ans
  case "$ans" in
    [Yy]*) CONFIRM=yes ;;
    *) echo "Aborted."; exit 0 ;;
  esac
fi

echo "Removing stopped containers..."
docker container prune -f

echo "Removing dangling images..."
docker image prune -f

echo "Pruning build cache..."
docker builder prune -f

echo "Cleanup complete."
