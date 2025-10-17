# Zoom Rooms SDK Microservice - Docker Image
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    make \
    git \
    curl \
    unzip \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Download and extract Zoom Rooms SDK
ARG SDK_URL="https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64"
RUN echo "Downloading Zoom Rooms SDK..." && \
    curl -L "$SDK_URL" -o zrc_sdk.zip && \
    echo "Extracting SDK..." && \
    unzip -q zrc_sdk.zip && \
    rm zrc_sdk.zip && \
    ls -la

# Set library path for SDK
ENV LD_LIBRARY_PATH=/app/libs

# Copy wrapper source
COPY bindings ./bindings
COPY CMakeLists.txt ./CMakeLists.txt
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code BEFORE building bindings (so install doesn't get overwritten)
COPY service ./service

# Build the C++ bindings
RUN mkdir -p build && \
    cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

# Create data and logs directories
# /root/.zoom/data - CRITICAL: Contains paired room database (third_zrc_data.db)
# /root/.zoom/logs - SDK log files
RUN mkdir -p /root/.zoom/data /root/.zoom/logs

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the service
WORKDIR /app/service
CMD ["python", "app.py"]
