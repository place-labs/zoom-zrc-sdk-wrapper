# Data Persistence and Backup Guide

## Critical Data Storage

The Zoom Rooms SDK stores paired room credentials and configuration in a SQLite database. This data **MUST** be persisted across container updates, otherwise all rooms will need to be re-paired.

### What Gets Stored

The SDK stores the following in `~/.zoom/data/`:

| File | Purpose | Critical? |
|------|---------|-----------|
| `third_zrc_data.db` | SQLite database with paired room credentials, tokens, and configuration | **YES - MUST BACKUP** |
| `third_zrc_data.db-journal` | SQLite journal file (temporary) | No |

The SDK also creates logs in `~/.zoom/logs/`:
- `python_*.log` - Application logs
- `ZPController_WebService_*.log` - SDK internal logs
- `last_log_file_id.txt` - Log rotation state

## Docker Volume Configuration

### Named Volume (Recommended)

The `docker-compose.yml` uses a **named Docker volume** for persistent data:

```yaml
volumes:
  # CRITICAL: Persistent data volume
  - zrc-data:/root/.zoom/data
  # Optional: Logs on host
  - ./logs:/root/.zoom/logs

volumes:
  zrc-data:
    driver: local
```

**Advantages:**
- ✅ Data persists across container recreations
- ✅ Data persists across image updates
- ✅ Survives `docker-compose down`
- ✅ Easy to backup with Docker tools
- ✅ Managed by Docker

**Location on host:**
```bash
docker volume inspect wrapper_zrc-data
# Look for "Mountpoint" - usually: /var/lib/docker/volumes/wrapper_zrc-data/_data
```

## Backup and Restore

### Quick Backup

```bash
# Backup the data volume
docker run --rm \
  -v wrapper_zrc-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/zrc-data-backup-$(date +%Y%m%d).tar.gz -C /data .

# Result: zrc-data-backup-20251016.tar.gz
```

### Quick Restore

```bash
# Stop the service
docker-compose down

# Restore from backup
docker run --rm \
  -v wrapper_zrc-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/zrc-data-backup-20251016.tar.gz"

# Start the service
docker-compose up -d
```

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups"
VOLUME_NAME="wrapper_zrc-data"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/zrc-data-$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Backing up $VOLUME_NAME to $BACKUP_FILE..."
docker run --rm \
  -v $VOLUME_NAME:/data:ro \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine tar czf /backup/zrc-data-$DATE.tar.gz -C /data .

echo "✓ Backup complete: $BACKUP_FILE"
echo "Size: $(du -h $BACKUP_FILE | cut -f1)"

# Keep only last 7 backups
ls -t $BACKUP_DIR/zrc-data-*.tar.gz | tail -n +8 | xargs -r rm
echo "✓ Old backups cleaned (kept last 7)"
```

Usage:
```bash
chmod +x backup.sh
./backup.sh
```

### Schedule Automatic Backups

Using cron:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /home/steve/projects/zoom/wrapper && ./backup.sh >> ./backups/backup.log 2>&1
```

## Updating the Container

### Safe Update Procedure

```bash
# 1. Backup current data
./backup.sh

# 2. Pull latest code
git pull

# 3. Rebuild image
docker-compose build

# 4. Recreate container (data volume persists!)
docker-compose up -d

# 5. Verify rooms restored
curl http://localhost:8000/api/rooms
```

The `zrc-data` volume persists through:
- ✅ `docker-compose up -d --force-recreate`
- ✅ `docker-compose down` followed by `docker-compose up -d`
- ✅ Image rebuilds (`docker-compose build`)
- ✅ Container deletions

**Data is only lost if you explicitly delete the volume:**
```bash
# This WILL delete paired room data!
docker-compose down -v  # ⚠️  WARNING: -v deletes volumes!
```

## Alternative: Host-Mounted Directory

If you prefer to see the data directly on the host filesystem:

```yaml
# In docker-compose.yml
volumes:
  # Use host directory instead of named volume
  - ./data:/root/.zoom/data
  - ./logs:/root/.zoom/logs
```

**Advantages:**
- Easy to inspect files directly
- Simple backup with standard tools
- Clear where data is stored

**Disadvantages:**
- Permission issues on some systems
- Less portable across environments

**Backup with host mount:**
```bash
# Simple backup
tar czf zrc-data-backup-$(date +%Y%m%d).tar.gz ./data

# Restore
tar xzf zrc-data-backup-20251016.tar.gz
```

## Migration Between Setups

### From Named Volume to Host Directory

```bash
# 1. Stop service
docker-compose down

# 2. Extract data from volume
docker run --rm \
  -v wrapper_zrc-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/temp-data.tar.gz -C /data .

# 3. Extract to host directory
mkdir -p ./data
tar xzf temp-data.tar.gz -C ./data
rm temp-data.tar.gz

# 4. Update docker-compose.yml to use ./data
# (See example above)

# 5. Start service
docker-compose up -d
```

### From Host Directory to Named Volume

```bash
# 1. Stop service
docker-compose down

# 2. Create volume and populate
docker volume create wrapper_zrc-data
docker run --rm \
  -v wrapper_zrc-data:/data \
  -v $(pwd)/data:/host-data:ro \
  alpine cp -a /host-data/. /data/

# 3. Update docker-compose.yml to use named volume
# (See example above)

# 4. Start service
docker-compose up -d
```

## Inspecting the Database

The `third_zrc_data.db` is a SQLite3 database. You can inspect it:

```bash
# Copy database out of container
docker cp zrc-microservice:/root/.zoom/data/third_zrc_data.db ./

# Or from named volume
docker run --rm \
  -v wrapper_zrc-data:/data \
  -v $(pwd):/backup \
  alpine cp /data/third_zrc_data.db /backup/

# Inspect with sqlite3
sqlite3 third_zrc_data.db

# List tables
.tables

# View schema
.schema

# Query data (example)
SELECT * FROM rooms;
```

**⚠️ Warning:** Do NOT modify the database directly unless you know what you're doing. Let the SDK manage it.

## Troubleshooting

### "No previously paired rooms found" after update

**Cause:** Data volume was not persisted or was deleted.

**Solution:**
1. Check if volume exists: `docker volume ls | grep zrc-data`
2. Check volume contents:
   ```bash
   docker run --rm -v wrapper_zrc-data:/data alpine ls -la /data
   ```
3. Restore from backup (see above)

### Volume permissions issues

**Issue:** SDK can't write to volume (permission denied)

**Solution:**
```bash
# Fix permissions on named volume
docker run --rm -v wrapper_zrc-data:/data alpine chown -R 0:0 /data

# Or on host directory
sudo chown -R $(id -u):$(id -g) ./data
```

### Volume taking too much space

**Check size:**
```bash
docker system df -v | grep zrc-data
```

**Clean logs but keep data:**
```bash
docker exec zrc-microservice sh -c "rm -f /root/.zoom/logs/*.log"
```

## Best Practices

1. **Backup before updates**
   ```bash
   ./backup.sh
   docker-compose up -d
   ```

2. **Test backups regularly**
   ```bash
   # On dev/staging environment
   docker-compose down
   # Restore backup
   docker-compose up -d
   # Verify rooms: curl http://localhost:8000/api/rooms
   ```

3. **Monitor disk usage**
   ```bash
   docker system df -v
   ```

4. **Keep backup history**
   - 7 daily backups (automated in backup script)
   - 4 weekly backups (keep manually)
   - 12 monthly backups (keep manually)

5. **Secure backups**
   - Store backups on separate disk/server
   - Encrypt backups containing credentials
   - Set restrictive permissions: `chmod 600 zrc-data-backup-*.tar.gz`

6. **Document room pairings**
   - Keep a list of which rooms are paired
   - Record activation codes securely (for re-pairing if needed)
   - Document room IDs and display names

## Disaster Recovery

If all backups are lost:

1. **Re-pair all rooms manually:**
   ```bash
   # For each room
   curl -X POST http://localhost:8000/api/rooms/room1/pair \
     -H "Content-Type: application/json" \
     -d '{"activation_code": "YOUR-ACTIVATION-CODE"}'
   ```

2. **Get new activation codes from Zoom admin portal**
   - Log into Zoom Rooms admin portal
   - Navigate to each room
   - Generate new pairing code
   - Use API to pair

3. **Immediately backup after re-pairing:**
   ```bash
   ./backup.sh
   ```

## Related Documentation

- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [SELF_CONTAINED_SETUP.md](SELF_CONTAINED_SETUP.md) - Setup guide
- [STATUS.md](STATUS.md) - Features and status

## Summary

**Critical Files:**
- `/root/.zoom/data/third_zrc_data.db` - Paired room database

**Docker Volume:**
- Named volume: `wrapper_zrc-data`
- Persists across updates automatically

**Backup Command:**
```bash
docker run --rm -v wrapper_zrc-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /data .
```

**Restore Command:**
```bash
docker run --rm -v wrapper_zrc-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/backup.tar.gz"
```

**⚠️ Remember:** Always backup before updating containers!
