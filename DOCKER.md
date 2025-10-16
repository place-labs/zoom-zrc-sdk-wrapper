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
