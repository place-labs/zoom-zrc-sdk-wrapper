#!/bin/bash
# Update script for new Zoom Rooms SDK versions
# Run this after replacing the SDK files (include/, libs/)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Zoom Rooms SDK Update Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Check SDK files exist
echo -e "${BLUE}[1/4] Checking SDK files...${NC}"
if [ ! -d "../include" ]; then
    echo -e "${YELLOW}ERROR: SDK include/ directory not found${NC}"
    exit 1
fi
if [ ! -d "../libs" ]; then
    echo -e "${YELLOW}ERROR: SDK libs/ directory not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SDK files found${NC}"
echo ""

# Step 2: Regenerate bindings
echo -e "${BLUE}[2/4] Regenerating pybind11 bindings...${NC}"
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${YELLOW}Virtual environment not found, creating...${NC}"
    python3 -m venv .venv
    .venv/bin/pip install -q jinja2
fi
.venv/bin/python generator/simple_generator.py
echo -e "${GREEN}✓ Bindings regenerated${NC}"
echo ""

# Step 3: Rebuild C++ module
echo -e "${BLUE}[3/4] Rebuilding C++ Python module...${NC}"
rm -rf build/
./build.sh
echo -e "${GREEN}✓ Module rebuilt${NC}"
echo ""

# Step 4: Verify installation
echo -e "${BLUE}[4/4] Verifying installation...${NC}"
if [ -f "service/zrc_sdk.*.so" ] || [ -f "service/zrc_sdk.so" ]; then
    echo -e "${GREEN}✓ Module installed successfully${NC}"
else
    echo -e "${YELLOW}WARNING: Module file not found in service/${NC}"
    echo -e "${YELLOW}Build may have failed${NC}"
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
