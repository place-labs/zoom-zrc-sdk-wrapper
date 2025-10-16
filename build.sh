#!/bin/bash
# Build script for Zoom Rooms SDK Python wrapper

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Zoom Rooms SDK Python wrapper...${NC}"

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo -e "${BLUE}Configuring CMake...${NC}"
cmake ..

# Build
echo -e "${BLUE}Building C++ bindings...${NC}"
make -j$(nproc)

# Install to service directory
echo -e "${BLUE}Installing module to service directory...${NC}"
make install

echo -e "${GREEN}Build complete! Python module installed to: ${SCRIPT_DIR}/service/${NC}"
echo -e "${GREEN}Run 'cd service && python3 -c \"import zrc_sdk; print(zrc_sdk)\"' to test${NC}"
