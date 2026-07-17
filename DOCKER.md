# Docker Deployment Guide

This guide explains how to build and run the Zoom Rooms SDK Microservice using Docker.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Zoom Rooms SDK libraries and headers in parent directory (`../libs` and `../include`)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using Docker Commands

```bash
# Build the image (from parent directory)
cd /home/steve/projects/zoom
docker build -f wrapper/Dockerfile -t zrc-microservice:latest .

# Run the container
docker run -d \
  --name zrc-microservice \
  -p 8000:8000 \
  -v ./wrapper/logs:/root/.zoom/logs \
  zrc-microservice:latest

# View logs
docker logs -f zrc-microservice

# Stop and remove
docker stop zrc-microservice
docker rm zrc-microservice
```

## Configuration

### Port Mapping

By default, the service exposes port **8000**. You can change this in `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"  # Maps host port 9000 to container port 8000
```

### Volume Mounts

The Docker setup includes a volume mount for persistent logs:

```yaml
volumes:
  - ./logs:/root/.zoom/logs
```

This ensures SDK logs are preserved across container restarts.

### Development Mode

To mount the service code for live development, uncomment this line in `docker-compose.yml`:

```yaml
volumes:
  - ./service:/app/service  # Hot reload for development
```

## Testing the Service

Once the container is running, test the API endpoints:

```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# List rooms
curl http://localhost:8000/api/rooms

# API documentation (browser)
open http://localhost:8000/docs
```

## Container Health Check

The Docker image includes a built-in health check that runs every 30 seconds:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' zrc-microservice

# View health check logs
docker inspect --format='{{json .State.Health}}' zrc-microservice | jq
```

## Troubleshooting

### Container won't start

Check the logs:
```bash
docker logs zrc-microservice
```

Common issues:
- Port 8000 already in use → Change port mapping
- SDK library path issues → Verify libs are copied correctly

### SDK initialization fails

Ensure the SDK libraries and headers are in the correct locations:
```bash
docker exec zrc-microservice ls -l /opt/zoomsdk/libs
docker exec zrc-microservice ls -l /opt/zoomsdk/include/include
```

### Permission issues with logs

The container runs as root by default. Logs directory needs proper permissions:
```bash
chmod 755 ./logs
```

### Pairing fails with error code 100 ("fail to connect to room")

`POST /api/rooms/{id}/pair` returns `Pairing failed with error code: 100`, and the
logs show `OnPairRoomResult: 100`.

**What 100 means here:** In the `OnPairRoomResult` callback, `100` is **"fail to
connect to room"** — *not* `ZRCSDKERR_DEVICE_NOT_EXIST` (that is the value `100` in
the *global* `ZRCSDKError` enum, a different code space). The pairing callback has
its own codes: `0` success, `30055016` invalid/used activation code, and
`100`/`101`/`102` for connect / verify failures. So a `100` means the activation
code was **accepted** and the SDK then failed to open its direct connection to the
Zoom Room compute. A bad or already-used code returns `30055016` instead.

**Root cause (Docker):** After the cloud validates the code, the SDK connects
directly to the ZR compute over the local/routed network. Pairing therefore
requires **IP reachability from this container to the ZR compute** (observed on
ports 80/443). The common failure is a **subnet collision**: Docker's default
bridge is `172.17.0.0/16`, and if the ZR lives in that range (e.g.
`172.17.193.172`), the container — and the Docker Desktop VM itself — treat the ZR
as on-link, ARP into the void, and never route the packet out to the host/VPN. The
result is `EHOSTUNREACH`/timeout surfaced as pair code `100`.

**Diagnose** — from inside the container, check you can actually reach the ZR:
```bash
docker exec <container> python -c \
'import socket;s=socket.socket();s.settimeout(6);s.connect(("<ZR_IP>",443));print("REACHABLE")'
```
If this fails while the host succeeds, it is a routing/collision problem, not the
SDK or the activation code.

**Fix** — move Docker off the colliding range (values must not overlap the ZR/VPN
subnet). In `~/.docker/daemon.json` (Docker Desktop → Settings → Docker Engine):
```json
{
  "bip": "10.200.0.1/24",
  "default-address-pools": [ { "base": "10.201.0.0/16", "size": 24 } ]
}
```
Restart Docker, recreate the container, and re-run the reachability check above
before pairing. On Docker Desktop for Mac this also lets the gVisor proxy forward
the traffic over the host's VPN once the ZR IP is no longer on-link.

> Note: the controller does **not** need to be on the *same* subnet as the ZR —
> a routed/VPN path works fine. It needs to *reach* the ZR, and its Docker subnets
> must **not overlap** the ZR's subnet.

## Image Details

- **Base Image**: `python:3.11-slim`
- **Image Size**: ~450 MB (includes SDK, Python, and build tools)
- **SDK Location**: `/opt/zoomsdk/`
- **Service Location**: `/app/service/`
- **Library Path**: `LD_LIBRARY_PATH=/opt/zoomsdk/libs`

## Building from Scratch

If you need to rebuild completely:

```bash
# Remove existing container and image
docker-compose down
docker rmi zrc-microservice:latest

# Clear Docker cache and rebuild
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

## Production Considerations

### Resource Limits

Add resource constraints in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

### Restart Policy

The service is configured with `restart: unless-stopped` by default. For production, consider:

```yaml
restart: always  # Always restart on failure
```

### Logging

Configure Docker logging to prevent disk space issues:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Security

For production deployment:
1. Run as non-root user (add `USER` directive to Dockerfile)
2. Use secrets management for sensitive configuration
3. Enable TLS/SSL via reverse proxy (nginx, traefik)
4. Implement authentication layer

## Networking

The service uses a custom bridge network (`zrc-network`). To connect other containers:

```yaml
services:
  my-app:
    networks:
      - zrc-network

networks:
  zrc-network:
    external: true
    name: wrapper_zrc-network
```

> **Important — subnet must not overlap the Zoom Room.** Pairing opens a direct
> connection from this service to the ZR compute, so the container needs IP
> reachability to the ZR *and* its Docker subnets must not collide with the ZR's
> network. If the ZR lives in `172.17.0.0/16` (Docker's default bridge range),
> change Docker's `bip`/`default-address-pools` to a non-overlapping range (e.g.
> `10.200.0.0/24` / `10.201.0.0/16`). See *Troubleshooting → Pairing fails with
> error code 100*.

## Environment Variables

You can pass environment variables in `docker-compose.yml`:

```yaml
environment:
  - LOG_LEVEL=DEBUG
  - MAX_ROOMS=10
```

## Updating the Service

To update the service code:

```bash
# Pull latest changes
git pull

# Rebuild image
docker-compose build

# Recreate container
docker-compose up -d --force-recreate
```

## Monitoring

### View real-time logs

```bash
docker-compose logs -f --tail=100
```

### Check resource usage

```bash
docker stats zrc-microservice
```

### Inspect container

```bash
docker inspect zrc-microservice
```

## Backup and Restore

### Backup SDK data

```bash
# Backup logs and paired room data
docker exec zrc-microservice tar czf /tmp/backup.tar.gz /root/.zoom/
docker cp zrc-microservice:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

### Restore data

```bash
# Restore from backup
docker cp ./backup.tar.gz zrc-microservice:/tmp/
docker exec zrc-microservice tar xzf /tmp/backup.tar.gz -C /
docker restart zrc-microservice
```

## Support

For issues with:
- **Docker setup**: Check this documentation
- **SDK functionality**: Refer to Zoom Rooms SDK documentation
- **Service code**: See main STATUS.md

## Related Documentation

- [STATUS.md](STATUS.md) - Build status and feature documentation
- [docker-compose.yml](docker-compose.yml) - Service configuration
- [Dockerfile](Dockerfile) - Image build instructions
