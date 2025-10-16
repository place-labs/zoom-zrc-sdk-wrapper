#!/bin/bash
# Backup script for Zoom Rooms SDK persistent data
set -e

BACKUP_DIR="./backups"
VOLUME_NAME="wrapper_zrc-data"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/zrc-data-$DATE.tar.gz"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Backing up Zoom Rooms SDK data...${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup the volume
echo "Creating backup: $BACKUP_FILE"
docker run --rm \
  -v $VOLUME_NAME:/data:ro \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine tar czf /backup/zrc-data-$DATE.tar.gz -C /data .

# Check if backup was created
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup complete: $BACKUP_FILE${NC}"
    echo -e "${GREEN}✓ Size: $SIZE${NC}"

    # List contents
    echo ""
    echo "Backup contains:"
    tar tzf "$BACKUP_FILE" | grep -E '\.(db|txt)$' || true

    # Keep only last 7 backups
    echo ""
    echo "Cleaning old backups (keeping last 7)..."
    ls -t $BACKUP_DIR/zrc-data-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
    REMAINING=$(ls -1 $BACKUP_DIR/zrc-data-*.tar.gz 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Backups in $BACKUP_DIR: $REMAINING${NC}"
else
    echo -e "\033[0;31m✗ Backup failed!${NC}"
    exit 1
fi
