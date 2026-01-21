#!/bin/bash
# Update script for Zoom Rooms SDK
# Updates the sdk-version.lock to the latest release and rebuilds

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# SDK URL (latest release endpoint)
LATEST_SDK_URL="https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64"
LOCK_FILE="$SCRIPT_DIR/sdk-version.lock"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Zoom Rooms SDK Update Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Resolve the latest URL to get the versioned URL
echo -e "${BLUE}[1/5] Resolving latest SDK version...${NC}"
VERSIONED_URL=$(curl -Ls -o /dev/null -w '%{url_effective}' "$LATEST_SDK_URL")
if [ -z "$VERSIONED_URL" ] || [ "$VERSIONED_URL" = "$LATEST_SDK_URL" ]; then
    echo -e "${RED}ERROR: Could not resolve versioned URL from latest endpoint${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Resolved to: $VERSIONED_URL${NC}"
echo "$VERSIONED_URL" > "$LOCK_FILE"
echo -e "${GREEN}✓ Lock file updated${NC}"
echo ""

# Step 2: Clean existing SDK files to force fresh download
echo -e "${BLUE}[2/5] Cleaning existing SDK files...${NC}"
rm -rf libs/ include/ zrc_sdk.zip
echo -e "${GREEN}✓ SDK files cleaned${NC}"
echo ""

# Step 3: Download and build using build.sh
echo -e "${BLUE}[3/5] Downloading SDK and building...${NC}"
./build.sh
echo -e "${GREEN}✓ SDK downloaded and built${NC}"
echo ""

# Step 4: Regenerate bindings
echo -e "${BLUE}[4/5] Regenerating pybind11 bindings...${NC}"
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${YELLOW}Virtual environment not found, creating...${NC}"
    python3 -m venv .venv
    .venv/bin/pip install -q jinja2
fi
.venv/bin/python generator/simple_generator.py
echo -e "${GREEN}✓ Bindings regenerated${NC}"
echo ""

# Step 5: Rebuild with new bindings
echo -e "${BLUE}[5/5] Rebuilding with updated bindings...${NC}"
rm -rf build/
./build.sh
echo -e "${GREEN}✓ Module rebuilt${NC}"
echo ""

# Verify installation
shopt -s nullglob
module_candidates=(service/zrc_sdk*.so)
shopt -u nullglob
if [ ${#module_candidates[@]} -gt 0 ]; then
    echo -e "${GREEN}✓ Module installed successfully${NC}"
    latest_module=""
    for candidate in "${module_candidates[@]}"; do
        if [ -z "$latest_module" ] || [ "$candidate" -nt "$latest_module" ]; then
            latest_module="$candidate"
        fi
    done
    echo -e "${GREEN}  - ${latest_module}${NC}"
else
    echo -e "${RED}WARNING: Module file not found in service/${NC}"
    echo -e "${RED}Build may have failed${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ SDK update complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. cd service/"
echo "  2. Install Python dependencies: ../.venv/bin/pip install -r ../requirements.txt"
echo "  3. Run the service: ../.venv/bin/python app.py"
echo ""
