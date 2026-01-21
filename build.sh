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
LOCK_FILE="$SCRIPT_DIR/sdk-version.lock"
SDK_URL_CACHE="$SCRIPT_DIR/.sdk-url"
if [ ! -f "$LOCK_FILE" ]; then
    echo -e "\033[0;31mERROR: sdk-version.lock not found. Run update_sdk.sh first.${NC}"
    exit 1
fi
SDK_URL=$(cat "$LOCK_FILE" | tr -d '[:space:]')
SDK_ZIP="zrc_sdk.zip"

# Check if SDK needs to be downloaded/updated
NEED_DOWNLOAD=false
if [ ! -d "libs" ] || [ ! -d "include" ]; then
    NEED_DOWNLOAD=true
    echo -e "${YELLOW}Zoom Rooms SDK not found.${NC}"
elif [ ! -f "$SDK_URL_CACHE" ]; then
    NEED_DOWNLOAD=true
    echo -e "${YELLOW}SDK version cache not found, will verify SDK.${NC}"
elif [ "$(cat "$SDK_URL_CACHE" | tr -d '[:space:]')" != "$SDK_URL" ]; then
    NEED_DOWNLOAD=true
    echo -e "${YELLOW}SDK version mismatch detected. Updating SDK...${NC}"
    rm -rf libs/ include/ zrc_sdk.zip build/
fi

if [ "$NEED_DOWNLOAD" = true ]; then
    echo -e "${BLUE}Downloading SDK from Zoom...${NC}"
    curl -L "$SDK_URL" -o "$SDK_ZIP"

    # Extract SDK
    echo -e "${BLUE}Extracting SDK...${NC}"
    unzip -q -o "$SDK_ZIP"

    # Verify extraction
    if [ -d "libs" ] && [ -d "include" ]; then
        echo -e "${GREEN}✓ SDK extracted successfully${NC}"
        # Cache the URL we downloaded
        echo "$SDK_URL" > "$SDK_URL_CACHE"
    else
        echo -e "\033[0;31mERROR: SDK extraction failed. Expected libs/ and include/ directories.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ SDK already present and matches sdk-version.lock${NC}"
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
