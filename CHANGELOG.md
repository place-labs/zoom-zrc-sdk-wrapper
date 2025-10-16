# Changelog

## [1.1.0] - 2025-10-16 - Self-Contained Setup

### Major Changes

#### ✨ Fully Self-Contained Wrapper
- SDK is now automatically downloaded during build process
- No external dependencies - everything contained in wrapper/ directory
- Downloads SDK from: https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64

#### 📦 Git-Friendly Structure
- Added comprehensive .gitignore
- Excludes SDK binaries (Demo/, include/, libs/)
- Excludes build artifacts (build/, *.so)
- Only source code committed to version control

#### 🐳 Docker Improvements
- Dockerfile now downloads SDK automatically
- No need for parent directory context
- Self-contained build process
- Fixed LD_LIBRARY_PATH configuration

#### 📝 Documentation
- Added SELF_CONTAINED_SETUP.md - Complete setup guide
- Updated README.md with Docker-first approach
- Updated STATUS.md to reflect self-contained nature
- All docs emphasize automatic SDK download

### Modified Files

#### Build Scripts
- `build.sh` - Added automatic SDK download and extraction
- `run_service.sh` - Updated library paths to use local SDK
- `CMakeLists.txt` - Changed SDK paths from parent to local directory

#### Docker Configuration
- `Dockerfile` - Now downloads and extracts SDK during build
- `docker-compose.yml` - Updated context and library paths
- Fixed environment variable: `LD_LIBRARY_PATH=/app/libs`

#### Version Control
- `.gitignore` - Comprehensive exclusions for SDK and binaries

### Technical Details

#### SDK Download Process
```bash
# In build.sh
SDK_URL="https://nws.zoom.us/nws/pkg/1.0/package/download?identifier=us.zoom.ZRC.SDK.LINUX&arch=x86_64"
curl -L "$SDK_URL" -o zrc_sdk.zip
unzip -q -o zrc_sdk.zip
```

#### Directory Structure Changes
**Before:**
```
zoom/
├── include/          # SDK headers (manual)
├── libs/             # SDK libraries (manual)
└── wrapper/          # Wrapper code
```

**After:**
```
zoom/wrapper/         # Self-contained
├── include/          # Downloaded automatically
├── libs/             # Downloaded automatically
├── Demo/             # Downloaded automatically
└── [source files]    # Committed to git
```

### Testing

All functionality verified:
- ✅ Local build with automatic SDK download
- ✅ Docker build with automatic SDK download
- ✅ Service startup and API endpoints
- ✅ SDK initialization and room restoration
- ✅ Health checks passing

### Performance

- SDK download: 30.9 MB, 4-6 seconds
- Local build time: 10-15 seconds (after download)
- Docker build time: 60-90 seconds (including download)
- No performance degradation from previous version

### Migration Guide

If you have the old setup with SDK in parent directory:

```bash
# 1. Pull latest changes
cd /home/steve/projects/zoom/wrapper
git pull

# 2. Clean old build artifacts
rm -rf build service/*.so

# 3. Rebuild (automatically downloads SDK)
./build.sh

# 4. Run service
./run_service.sh
```

For Docker:
```bash
# 1. Pull latest changes
git pull

# 2. Rebuild with new Dockerfile
docker-compose build --no-cache

# 3. Start service
docker-compose up -d
```

### Known Issues

None. All previous functionality maintained.

### Breaking Changes

None. API remains unchanged. Only build process updated.

---

## [1.0.0] - 2025-10-16 - Initial Release

### Features

- ✅ pybind11 C++ bindings for Zoom Rooms SDK
- ✅ FastAPI REST API microservice
- ✅ Docker and docker-compose support
- ✅ Automatic room restoration on startup
- ✅ Multi-room support
- ✅ Health check endpoints
- ✅ SDK HeartBeat loop (150ms)

### SDK Methods Exposed

**Core SDK (IZRCSDK)**
- GetInstance()
- HeartBeat()
- CreateZoomRoomsService()
- RegisterSDKSink()
- QueryAllZoomRoomsServices()

**Room Service (IZoomRoomsService)**
- PairRoomWithActivationCode()
- UnpairRoom()
- RetryToPairRoom()
- GetMeetingService()
- GetPreMeetingService()

**Meeting Service (IMeetingService)**
- StartInstantMeeting()
- JoinMeeting()
- ExitMeeting()

**Pre-Meeting Service (IPreMeetingService)**
- GetConnectionState()

### Documentation

- README.md - Quick start and API usage
- STATUS.md - Build status and features
- DOCKER.md - Docker deployment guide
- DOCKER_DEPLOYMENT_SUMMARY.md - Docker technical details
