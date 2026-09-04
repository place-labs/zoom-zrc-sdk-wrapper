#!/bin/bash
# Local build/compile check — and optional local (re)deploy.
#
#   ./build_test.sh          Build the linux/amd64 image (compile check, same as CI).
#                            Touches nothing that's running — safe as a pre-commit gate.
#   ./build_test.sh --run    After a SUCCESSFUL build, swap the local container onto the
#                            fresh image so you can hit it at http://localhost:8000.
#
# The Zoom SDK ships only Linux x86_64 libs, so the module must compile inside a
# linux/amd64 container. On Apple Silicon that runs under QEMU emulation (slower,
# but identical to CI). Requires Docker Desktop to be running.
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

IMAGE="zrc-build-check"
CONTAINER="zrc-live"

RUN=false
case "${1:-}" in
    -r|--run) RUN=true ;;
    "")       ;;
    *)        echo -e "${RED}Unknown option: $1  (use --run to also start the container)${NC}"; exit 1 ;;
esac

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Start Docker Desktop and retry.${NC}"
    exit 1
fi

echo -e "${BLUE}Compiling bindings in a linux/amd64 container (same as CI)...${NC}"
echo -e "${BLUE}(On Apple Silicon this emulates x86_64 — expect a few minutes.)${NC}"

# Build first. If this fails we exit BEFORE touching any running container.
if ! docker build --platform linux/amd64 -t "$IMAGE" .; then
    echo -e "${RED}✗ Build FAILED — fix the compile errors above. Running container left untouched.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build succeeded — bindings compile cleanly.${NC}"

if [ "$RUN" = false ]; then
    echo -e "${GREEN}  (run './build_test.sh --run' to (re)start the local container on this image)${NC}"
    exit 0
fi

# --- Deploy locally. Only reached after a successful build, so a broken build never
# --- tears down your instance. The zrc-data volume preserves the paired-room DB.
echo -e "${BLUE}Swapping local container '${CONTAINER}' onto the fresh image...${NC}"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
# Local dev uses a DISTINCT device identity so it never collides with the deployed
# pod's identity (a shared serial/MAC causes pairing to fail with DEVICE_NOT_EXIST).
docker run -d --name "$CONTAINER" -p 8000:8000 \
    -v zrc-data:/root/.zoom/data \
    -e ZRC_DEVICE_SERIAL="SDK-WRAPPER-LOCAL" \
    -e ZRC_DEVICE_MAC="02:00:00:00:00:01" \
    --platform linux/amd64 "$IMAGE" >/dev/null

echo -e "${BLUE}Waiting for the service to come up...${NC}"
for _ in $(seq 1 20); do
    sleep 2
    if H=$(curl -sf http://localhost:8000/health 2>/dev/null); then
        echo -e "${GREEN}✓ Up: ${H}${NC}"
        echo -e "${GREEN}  REST : http://localhost:8000${NC}"
        echo -e "${GREEN}  WS   : ws://localhost:8000/api/rooms/{room_id}/events${NC}"
        echo -e "${GREEN}  (reconnect your WebSocket — the old connection dropped with the old container)${NC}"
        exit 0
    fi
done
echo -e "${RED}Service did not report healthy in time. Recent logs:${NC}"
docker logs --tail 20 "$CONTAINER"
exit 1
