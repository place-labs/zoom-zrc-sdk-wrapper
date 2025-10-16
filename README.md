# Zoom Rooms SDK Microservice

A lightweight Python microservice wrapper around the Zoom Rooms C++ SDK. Exposes all SDK functionality via REST API + WebSocket for real-time events.

## Architecture

```
┌─────────────────────────────────────┐
│  Your Web Application               │
└─────────────┬───────────────────────┘
              │ HTTP REST + WebSocket
              ▼
┌─────────────────────────────────────┐
│  FastAPI Microservice (Python)      │
│  - Multi-room state management      │
│  - Event broadcasting               │
│  - HeartBeat timer                  │
└─────────────┬───────────────────────┘
              │ Python bindings
              ▼
┌─────────────────────────────────────┐
│  pybind11 C++ Bindings              │
│  (auto-generated)                   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Zoom Rooms C++ SDK                 │
└─────────────────────────────────────┘
```

## Features

- **Thinnest possible wrapper** - Direct 1:1 mapping of SDK methods to REST endpoints
- **Auto-generated bindings** - Easy to update when new SDK versions are released
- **Multi-room support** - Control multiple Zoom Rooms simultaneously
- **Real-time events** - WebSocket channels for SDK callbacks
- **Per-room state management** - Each room maintains independent state
- **No authentication layer** - Delegates auth to your main web service

## Project Structure

```
wrapper/
├── bindings/              # Generated C++ pybind11 code
│   └── zrc_bindings.cpp  # Auto-generated, don't edit
├── generator/             # Binding generator scripts
│   └── simple_generator.py
├── service/               # FastAPI microservice
│   └── app.py            # Main service implementation
├── build/                 # CMake build directory (created during build)
├── .venv/                 # Python virtual environment
├── CMakeLists.txt         # Build configuration
├── requirements.txt       # Python dependencies
├── build.sh               # Build the C++ module
├── run_service.sh         # Start the microservice
├── update_sdk.sh          # Regenerate bindings for new SDK version
└── README.md              # This file
```

## Quick Start

### 1. Build the C++ Python Module

```bash
cd wrapper
./build.sh
```

This will:
- Download pybind11 (if needed)
- Compile the C++ bindings
- Install the `zrc_sdk` Python module to `service/`

### 2. Run the Microservice

```bash
./run_service.sh
```

The service will start on `http://localhost:8000`

- **API documentation**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/

## API Usage

### Pairing a Room

```bash
curl -X POST http://localhost:8000/api/rooms/room1/pair \
  -H "Content-Type: application/json" \
  -d '{"activation_code": "123-456-789"}'
```

Response:
```json
{
  "room_id": "room1",
  "result": 0,
  "success": true
}
```

### Starting an Instant Meeting

```bash
curl -X POST http://localhost:8000/api/rooms/room1/meeting/start_instant
```

### Joining a Meeting

```bash
curl -X POST http://localhost:8000/api/rooms/room1/meeting/join \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_number": "123456789",
    "password": "optional"
  }'
```

### Muting Audio

```bash
# Mute
curl -X POST "http://localhost:8000/api/rooms/room1/audio/mute?mute=true"

# Unmute
curl -X POST "http://localhost:8000/api/rooms/room1/audio/mute?mute=false"
```

### Muting Video

```bash
curl -X POST "http://localhost:8000/api/rooms/room1/video/mute?mute=true"
```

### Exiting a Meeting

```bash
curl -X POST http://localhost:8000/api/rooms/room1/meeting/exit
```

### Listing Rooms

```bash
curl http://localhost:8000/api/rooms
```

## Real-Time Events (WebSocket)

Connect to WebSocket for real-time SDK event notifications:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/rooms/room1/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event received:', data);
};

// Example events:
// {"event": "OnPairRoomResult", "result": 0}
// {"event": "OnUpdateMeetingStatus", "status": "InMeeting"}
// {"event": "OnZRConnectionStateChanged", "state": "ConnectionStateConnected"}
// {"event": "OnConfReadyNotification"}
// {"event": "OnExitMeetingNotification"}
```

### Python WebSocket Client Example

```python
import asyncio
import websockets
import json

async def listen_to_room_events():
    uri = "ws://localhost:8000/api/rooms/room1/events"
    async with websockets.connect(uri) as websocket:
        print("Connected to room events")
        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event}")

asyncio.run(listen_to_room_events())
```

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/` | Health check |
| GET    | `/api/rooms` | List all paired rooms |
| POST   | `/api/rooms/{room_id}/pair` | Pair a room with activation code |
| POST   | `/api/rooms/{room_id}/unpair` | Unpair a room |
| POST   | `/api/rooms/{room_id}/meeting/start_instant` | Start instant meeting |
| POST   | `/api/rooms/{room_id}/meeting/join` | Join meeting by number |
| POST   | `/api/rooms/{room_id}/meeting/exit` | Exit meeting |
| POST   | `/api/rooms/{room_id}/audio/mute` | Mute/unmute audio |
| POST   | `/api/rooms/{room_id}/video/mute` | Mute/unmute video |
| WS     | `/api/rooms/{room_id}/events` | WebSocket event stream |

See full interactive API docs at http://localhost:8000/docs

## Updating to New SDK Versions

When a new Zoom Rooms SDK version is released:

1. Replace SDK files:
   ```bash
   # Backup old SDK
   mv ../include ../include.old
   mv ../libs ../libs.old

   # Copy new SDK
   cp -r /path/to/new/sdk/include ../include
   cp -r /path/to/new/sdk/libs ../libs
   ```

2. Run the update script:
   ```bash
   cd wrapper
   ./update_sdk.sh
   ```

This will:
- Regenerate pybind11 bindings
- Rebuild the C++ module
- Verify installation

3. Restart the service:
   ```bash
   ./run_service.sh
   ```

## Adding More SDK Methods

To expose additional SDK methods:

1. Edit `generator/simple_generator.py`
2. Add methods to the `SDK_CONFIG` dictionary
3. Regenerate bindings:
   ```bash
   .venv/bin/python generator/simple_generator.py
   ./build.sh
   ```
4. Add corresponding endpoints in `service/app.py`

### Example: Adding a New Method

```python
# In generator/simple_generator.py
SDK_CONFIG = {
    'IMeetingService': {
        'type': 'interface',
        'methods': [
            # ... existing methods ...
            'GetCurrentMeetingInfo() -> MeetingInfo',  # Add this
        ],
    },
}
```

Then in `service/app.py`:

```python
@app.get("/api/rooms/{room_id}/meeting/info")
async def get_meeting_info(room_id: str):
    room_service = room_manager.get_room_service(room_id)
    if not room_service:
        raise HTTPException(status_code=404, detail="Room not found")

    meeting_service = room_service.GetMeetingService()
    info = meeting_service.GetCurrentMeetingInfo()
    return {"meeting_info": info}
```

## Development

### Prerequisites

- Python 3.9+
- CMake 3.12+
- C++14 compiler (gcc/clang)
- Zoom Rooms C++ SDK

### Manual Build

```bash
cd wrapper

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Generate bindings
python generator/simple_generator.py

# Build C++ module
mkdir -p build && cd build
cmake ..
make -j$(nproc)
make install

# Run service
cd ../service
python app.py
```

### Testing

```bash
# Start the service
./run_service.sh

# In another terminal, test endpoints
curl http://localhost:8000/
curl -X POST http://localhost:8000/api/rooms/test/pair \
  -H "Content-Type: application/json" \
  -d '{"activation_code": "test"}'
```

## Architecture Details

### Per-Room State Management

Each Zoom Room gets:
- Independent `IZoomRoomsService` instance
- Separate callback handlers
- Dedicated WebSocket broadcast list
- Isolated state (connection, meeting status)

### HeartBeat Timer

The SDK requires `HeartBeat()` to be called every ~150ms on Linux. The microservice:
- Runs a single asyncio task for all rooms
- Calls SDK HeartBeat in a loop
- Starts on service startup
- Stops on shutdown

### Callback → Event Translation

SDK callbacks (C++) are translated to WebSocket events (JSON):

```cpp
// C++ SDK callback
void OnPairRoomResult(int32_t result) {
    // Handled by pybind11 trampoline
}
```

```python
# Python callback implementation
def OnPairRoomResult(self, result: int):
    # Broadcast to all WebSocket clients
    broadcast_event(room_id, {
        "event": "OnPairRoomResult",
        "result": result
    })
```

```javascript
// Client receives
ws.onmessage = (event) => {
    // {"event": "OnPairRoomResult", "result": 0}
}
```

## Troubleshooting

### Module not found: zrc_sdk

Run `./build.sh` to compile the C++ module.

### SDK library not found at runtime

Set `LD_LIBRARY_PATH`:
```bash
export LD_LIBRARY_PATH=/home/steve/projects/zoom/libs:$LD_LIBRARY_PATH
./run_service.sh
```

Or update CMakeLists.txt RPATH settings.

### HeartBeat not called / Callbacks not firing

Ensure the service is running (not crashed). The HeartBeat loop runs automatically in the background.

Check logs:
```
INFO:root:Starting SDK HeartBeat loop...
```

### WebSocket connection refused

Ensure the room exists (pair it first):
```bash
curl -X POST http://localhost:8000/api/rooms/room1/pair \
  -H "Content-Type: application/json" \
  -d '{"activation_code": "..."}'
```

Then connect:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/rooms/room1/events');
```

## License

This wrapper is provided as-is. Zoom Rooms SDK is subject to Zoom's licensing terms.

## Support

For SDK-specific questions, refer to the Zoom Rooms SDK documentation.

For wrapper issues, check:
1. Build succeeded: `ls service/zrc_sdk*.so`
2. Service running: `curl http://localhost:8000/`
3. Logs: Check console output

---

**Generated wrapper components:**
- C++ bindings: `bindings/zrc_bindings.cpp` (auto-generated)
- Python service: `service/app.py`
- Generator: `generator/simple_generator.py`
