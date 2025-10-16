# Self-Contained Setup - Complete Guide

The Zoom Rooms SDK Microservice is now fully self-contained within the `wrapper/` directory. No external SDK files are required - everything is downloaded automatically during the build process.

## Overview

This setup automatically:
- ✅ Downloads the Zoom Rooms SDK from Zoom's servers
- ✅ Extracts and configures the SDK locally
- ✅ Builds the Python bindings
- ✅ Creates a containerized microservice
- ✅ Excludes binaries from version control

## Prerequisites

### For Local Build
- Linux (x86_64)
- Python 3.11+
- CMake 3.12+
- g++ compiler
- curl and unzip
- Git

### For Docker Build
- Docker
- Docker Compose

## Directory Structure

```
wrapper/
├── .gitignore                    # Excludes SDK and build artifacts
├── build.sh                      # Automatically downloads SDK
├── Dockerfile                    # Self-contained Docker build
├── docker-compose.yml            # Service orchestration
├── CMakeLists.txt                # Build configuration
├── bindings/
│   └── zrc_bindings.cpp         # C++ bindings (committed)
├── service/
│   └── app.py                    # FastAPI service (committed)
└── requirements.txt              # Python dependencies (committed)

# Generated during build (not committed):
├── Demo/                         # SDK demo files
├── include/                      # SDK headers
├── libs/                         # SDK shared libraries
├── build/                        # Build artifacts
└── service/zrc_sdk*.so          # Compiled Python module
```

## What's Excluded from Git

The `.gitignore` file excludes:
- `Demo/`, `include/`, `libs/` - SDK directories (downloaded automatically)
- `*.zip` - SDK download file
- `build/` - Build artifacts
- `*.so` - Compiled shared libraries
- `__pycache__/`, `*.pyc` - Python cache files
- `.venv/`, `venv/` - Virtual environments
- `logs/` - Log files

## Quick Start

### Option 1: Docker (Recommended)

```bash
cd /home/steve/projects/zoom/wrapper

# Build and start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test the API
curl http://localhost:8000/health

# Stop the service
docker-compose down
```

**That's it!** Docker automatically:
1. Downloads the SDK from Zoom
2. Extracts it
3. Builds the C++ bindings
4. Installs Python dependencies
5. Starts the service

### Option 2: Local Build

```bash
cd /home/steve/projects/zoom/wrapper

# Build (automatically downloads SDK)
./build.sh

# Run the service
./run_service.sh
```

The `build.sh` script automatically:
1. Checks if SDK is present
2. Downloads it if missing (30.9 MB)
3. Extracts Demo/, include/, and libs/
4. Builds the Python module
5. Installs it to service/

## How It Works

### Automatic SDK Download

Both `build.sh` and `Dockerfile` download the SDK from:
```
https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64
```

The SDK is cached locally after the first download:
- **Local build**: Checks for `libs/` and `include/` directories, skips download if present
- **Docker build**: Downloads fresh SDK each time during image build (ensures latest version)

### Build Process

#### Local Build (`build.sh`)
```bash
# 1. Check for SDK
if [ ! -d "libs" ] || [ ! -d "include" ]; then
    # Download SDK if missing
    curl -L "$SDK_URL" -o zrc_sdk.zip
    unzip -q -o zrc_sdk.zip
fi

# 2. Build with CMake
mkdir -p build && cd build
cmake ..
make -j$(nproc)
make install  # Installs to service/
```

#### Docker Build
```dockerfile
# 1. Install build tools
RUN apt-get install cmake g++ make git curl unzip libatomic1

# 2. Download and extract SDK
RUN curl -L "$SDK_URL" -o zrc_sdk.zip && \
    unzip -q zrc_sdk.zip && \
    rm zrc_sdk.zip

# 3. Build bindings
RUN cmake .. && make -j$(nproc) && make install

# 4. Install Python deps
RUN pip install -r requirements.txt
```

### SDK Contents

After extraction, you'll have:
- **`Demo/`** - Example code and helper libraries
- **`include/`** - C++ header files for the SDK
- **`libs/libZRCSdk.so`** - Main SDK shared library (97 MB)

## Version Control Strategy

### What's Committed to Git
- Source code: `bindings/zrc_bindings.cpp`, `service/app.py`
- Build scripts: `build.sh`, `Dockerfile`, `docker-compose.yml`
- Configuration: `CMakeLists.txt`, `requirements.txt`, `.gitignore`
- Documentation: `*.md` files

### What's Not Committed
- SDK files (downloaded automatically)
- Build artifacts (generated during build)
- Virtual environments (created by user)
- Log files (runtime generated)

This ensures:
- ✅ Clean repository (no large binaries)
- ✅ Always use latest SDK version
- ✅ Reproducible builds
- ✅ Easy collaboration

## Updating the SDK

The SDK is automatically downloaded during each build. To force a fresh download:

### Local Build
```bash
# Remove existing SDK
rm -rf Demo/ include/ libs/ zrc_sdk.zip build/

# Rebuild (downloads fresh SDK)
./build.sh
```

### Docker Build
```bash
# Docker always downloads fresh SDK during build
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### SDK Download Fails

**Issue**: `curl: (6) Could not resolve host`

**Solution**:
- Check internet connection
- Verify Zoom's SDK URL is still active
- Try manual download and extract

### Build Fails with "SDK not found"

**Issue**: `ERROR: SDK extraction failed`

**Solution**:
```bash
# Check what was extracted
ls -la Demo/ include/ libs/

# Re-download manually
curl -L "https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64" -o zrc_sdk.zip
unzip -l zrc_sdk.zip  # List contents
unzip zrc_sdk.zip     # Extract
```

### Library Not Found at Runtime

**Issue**: `ImportError: libZRCSdk.so: cannot open shared object file`

**Solution**:
```bash
# Local: Check LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH  # Should include wrapper/libs

# Docker: Check environment variable in docker-compose.yml
# Should be: LD_LIBRARY_PATH=/app/libs
```

### Git Shows SDK Files as Changes

**Issue**: SDK directories appear in `git status`

**Solution**:
```bash
# Verify .gitignore is present
cat .gitignore | grep -E "Demo|include|libs"

# If missing, the directories shouldn't have been committed
# Remove them from git:
git rm -r --cached Demo/ include/ libs/
git commit -m "Remove SDK files from git"
```

## Performance Notes

### Download Size
- **SDK ZIP**: ~30.9 MB
- **Extracted SDK**: ~110 MB (mostly libZRCSdk.so)
- **Docker Image**: ~450 MB (includes OS, Python, build tools, SDK)

### Build Times
- **Local build**: 10-15 seconds (after SDK download)
- **Docker build**: 60-90 seconds (includes SDK download, dependency install)
- **SDK download**: 4-6 seconds (with good connection)

### Caching
- **Local**: SDK downloaded once, cached until manually deleted
- **Docker**: Each image build downloads fresh SDK (ensures latest version)

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          cd wrapper
          docker build -t zrc-microservice:test .

      - name: Test service
        run: |
          cd wrapper
          docker run -d -p 8000:8000 --name test zrc-microservice:test
          sleep 5
          curl http://localhost:8000/health
          docker stop test
```

### GitLab CI Example

```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - cd wrapper
    - docker build -t zrc-microservice:$CI_COMMIT_SHA .
    - docker run -d -p 8000:8000 --name test zrc-microservice:$CI_COMMIT_SHA
    - sleep 5
    - curl http://localhost:8000/health
```

## Security Considerations

### SDK Download
- Always downloaded over HTTPS
- From official Zoom domain (nws.zoom.us)
- No authentication required (public SDK)

### Docker Image
- Based on official `python:3.11-slim` image
- Build tools removed after build (use multi-stage for production)
- Runs as root by default (consider non-root user for production)

### Secrets
- No secrets required for SDK download
- API keys (if needed) should be passed via environment variables
- Never commit credentials to Git

## FAQ

**Q: Why not commit the SDK to Git?**
A: The SDK is ~110 MB and updates frequently. Downloading ensures latest version.

**Q: What if Zoom changes the download URL?**
A: Update the `SDK_URL` in both `build.sh` and `Dockerfile`.

**Q: Can I use a specific SDK version?**
A: Currently uses latest. To pin a version, download manually and comment out the download step.

**Q: Does this work on ARM/Mac?**
A: The Zoom SDK is x86_64 Linux only. Use Docker on ARM64 (Apple Silicon) with emulation.

**Q: How do I add the wrapper to Git?**
A: Just add the wrapper/ directory. The .gitignore ensures SDK files aren't committed.

## Related Documentation

- [STATUS.md](STATUS.md) - Build status and features
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [DOCKER_DEPLOYMENT_SUMMARY.md](DOCKER_DEPLOYMENT_SUMMARY.md) - Docker implementation details

## Support

For issues:
1. Check this documentation first
2. Verify SDK download is working: `curl -I "$SDK_URL"`
3. Check build logs for specific errors
4. Review `.gitignore` to ensure correct files are excluded
