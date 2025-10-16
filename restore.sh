#!/bin/bash
# Restore script for Zoom Rooms SDK persistent data
set -e

VOLUME_NAME="wrapper_zrc-data"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <backup-file.tar.gz>${NC}"
    echo ""
    echo "Available backups:"
    ls -1th backups/zrc-data-*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Restoring Zoom Rooms SDK data from backup...${NC}"
echo "Backup file: $BACKUP_FILE"
echo "Target volume: $VOLUME_NAME"
echo ""

# List what's in the backup
echo "Backup contains:"
tar tzf "$BACKUP_FILE" | grep -E '\.(db|txt)$' || true
echo ""

# Confirm
read -p "This will REPLACE all current data. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop the service
echo ""
echo -e "${YELLOW}Stopping service...${NC}"
docker-compose down

# Restore from backup
echo -e "${YELLOW}Restoring data...${NC}"
docker run --rm \
  -v $VOLUME_NAME:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && rm -rf ./* && tar xzf /backup/$BACKUP_FILE"

echo -e "${GREEN}✓ Data restored${NC}"

# Start the service
echo ""
echo -e "${YELLOW}Starting service...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Restore complete!${NC}"
echo ""
echo "Waiting for service to start..."
sleep 5

# Verify
echo "Verifying restored rooms:"
curl -s http://localhost:8000/api/rooms | python3 -m json.tool || true
