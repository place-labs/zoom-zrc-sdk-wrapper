#!/bin/bash
# Quick start script for the Zoom Rooms microservice

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Set library path for SDK
export LD_LIBRARY_PATH="$(cd .. && pwd)/libs:$LD_LIBRARY_PATH"

# Check if module is built
if [ ! -f "service/zrc_sdk."*".so" ] && [ ! -f "service/zrc_sdk.so" ]; then
    echo "ERROR: zrc_sdk module not found. Run './build.sh' first."
    exit 1
fi

# Check venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
.venv/bin/pip install -q -r requirements.txt

# Run the service
echo "Starting Zoom Rooms SDK microservice..."
echo "Library path: $LD_LIBRARY_PATH"
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

cd service
exec ../.venv/bin/python app.py
