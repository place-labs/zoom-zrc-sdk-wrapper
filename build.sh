#!/bin/bash
# Build script for Zoom Rooms SDK Python wrapper

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Zoom Rooms SDK Python wrapper...${NC}"

# SDK download URL and paths
SDK_URL="https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64"
SDK_ZIP="zrc_sdk.zip"

# Download and extract SDK if not present
if [ ! -d "libs" ] || [ ! -d "include" ]; then
    echo -e "${YELLOW}Zoom Rooms SDK not found. Downloading...${NC}"

    # Download SDK
    if [ ! -f "$SDK_ZIP" ]; then
        echo -e "${BLUE}Downloading SDK from Zoom...${NC}"
        curl -L "$SDK_URL" -o "$SDK_ZIP"
    else
        echo -e "${YELLOW}Using cached SDK zip file${NC}"
    fi

    # Extract SDK
    echo -e "${BLUE}Extracting SDK...${NC}"
    unzip -q -o "$SDK_ZIP"

    # Verify extraction
    if [ -d "libs" ] && [ -d "include" ]; then
        echo -e "${GREEN}✓ SDK extracted successfully${NC}"
    else
        echo -e "\033[0;31mERROR: SDK extraction failed. Expected libs/ and include/ directories.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ SDK already present${NC}"
fi

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
