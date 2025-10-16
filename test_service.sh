#!/bin/bash
# Test script to verify the microservice works

cd /home/steve/projects/zoom/wrapper

echo "Starting service in background..."
./run_service.sh > /tmp/zrc_test.log 2>&1 &
SERVICE_PID=$!

echo "Waiting for service to start..."
sleep 5

echo "Testing API endpoints..."
echo "1. Root endpoint:"
curl -s http://localhost:8000/ || echo "FAILED"

echo ""
echo "2. Health check:"
curl -s http://localhost:8000/health || echo "FAILED"

echo ""
echo "3. List rooms:"
curl -s http://localhost:8000/api/rooms || echo "FAILED"

echo ""
echo "Stopping service..."
kill $SERVICE_PID 2>/dev/null || true
wait $SERVICE_PID 2>/dev/null || true

echo ""
echo "Service log:"
cat /tmp/zrc_test.log | head -20

echo ""
echo "Test complete!"
