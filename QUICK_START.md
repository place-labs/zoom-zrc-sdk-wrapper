# Quick Start Guide

## 1. Build (one-time setup)

```bash
cd /home/steve/projects/zoom/wrapper
./build.sh
```

Wait for build to complete (~1-2 minutes).

## 2. Install Python Dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

## 3. Start the Service

```bash
./run_service.sh
```

Service starts on http://localhost:8000

## 4. Test It

Open http://localhost:8000/docs in your browser for interactive API documentation.

Or test with curl:

```bash
# Health check
curl http://localhost:8000/

# Pair a room
curl -X POST http://localhost:8000/api/rooms/myroom/pair \
  -H "Content-Type: application/json" \
  -d '{"activation_code": "YOUR-ACTIVATION-CODE"}'

# Start meeting
curl -X POST http://localhost:8000/api/rooms/myroom/meeting/start_instant
```

## 5. Listen to Events

```javascript
const ws = new WebSocket('ws://localhost:8000/api/rooms/myroom/events');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## That's It!

- **API docs**: http://localhost:8000/docs
- **Full README**: See README.md
- **Update SDK**: Run `./update_sdk.sh`
