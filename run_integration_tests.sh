#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo " TyriaVault - Integration Tests"
echo "========================================"
echo ""

echo "[1/6] Stopping previous containers..."
docker compose -f docker-compose.test.yml down -v 2>/dev/null || true

echo ""
echo "[2/6] Starting services (PostgreSQL and WireMock)..."
docker compose -f docker-compose.test.yml up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Error starting services with Docker Compose${NC}"
    exit 1
fi

echo ""
echo "[3/6] Waiting for services to be ready..."
sleep 5

echo ""
echo "[4/6] Initializing database..."
chmod +x app/tests/integration/setup_db.sh
./app/tests/integration/setup_db.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}Error initializing database${NC}"
    docker compose -f docker-compose.test.yml down -v
    exit 1
fi

echo ""
echo "[5/6] Starting application in background..."
export ENV=test
uvicorn app.main:api --host 0.0.0.0 --loop uvloop --port 8000 --env-file .env.test > /tmp/tyriavault_app.log 2>&1 &
APP_PID=$!
echo "Application started with PID: $APP_PID"

# Wait a bit for the application to start
echo "Waiting for application to start..."
sleep 5

echo ""
echo "[6/6] Running integration tests..."
pytest app/tests/integration/ -v -m integration --tb=short

TEST_RESULT=$?

echo ""
echo "========================================"
echo " Cleanup"
echo "========================================"

echo "Stopping services..."
docker compose -f docker-compose.test.yml down -v

echo "Stopping application (PID: $APP_PID)..."
kill $APP_PID 2>/dev/null || true

# Wait for process to terminate
sleep 2

# Force if still running
kill -9 $APP_PID 2>/dev/null || true

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} ✅ TESTS COMPLETED SUCCESSFULLY${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED} ❌ TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $TEST_RESULT

