#!/bin/bash
set -e

# Helper script to run SSL tests
# Usage: ./run-test.sh <test-number>
# Example: ./run-test.sh 1

TEST_NUM=$1

if [ -z "$TEST_NUM" ]; then
    echo "Usage: $0 <test-number>"
    echo "Available tests:"
    echo "  1 - SSL Disabled (backward compatibility)"
    echo "  2 - SSL Dual-Mode (HTTP + HTTPS)"
    echo "  3 - SSL with HTTP→HTTPS Redirect"
    echo "  4 - SSL with HSTS"
    exit 1
fi

COMPOSE_FILE="docker-compose.test${TEST_NUM}-*.yml"

echo "========================================="
echo "Running Test Scenario $TEST_NUM"
echo "========================================="
echo ""

# Stop any running containers
docker compose -f docker-compose.test*.yml down 2>/dev/null || true

# Start the test
docker compose -f $COMPOSE_FILE up -d

echo ""
echo "Waiting for nginx to start..."
sleep 3

echo ""
echo "Container logs:"
echo "========================================="
docker compose -f $COMPOSE_FILE logs
echo "========================================="
echo ""

case $TEST_NUM in
    1)
        echo "Test 1: HTTP on port 8080 (SSL disabled)"
        curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080/ || echo "Failed to connect"
        ;;
    2)
        echo "Test 2a: HTTP on port 8080"
        curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080/ || echo "Failed to connect"
        echo ""
        echo "Test 2b: HTTPS on port 8443"
        curl -k -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://localhost:8443/ || echo "Failed to connect"
        ;;
    3)
        echo "Test 3a: HTTP should redirect (301)"
        curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080/ || echo "Failed to connect"
        echo ""
        echo "Test 3b: HTTPS serves content"
        curl -k -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://localhost:8443/ || echo "Failed to connect"
        ;;
    4)
        echo "Test 4: HSTS header check"
        curl -k -s -I https://localhost:8443/ | grep -i "strict-transport-security" || echo "HSTS header not found"
        ;;
esac

echo ""
echo "Test completed. Container is still running."
echo "To stop: docker compose -f $COMPOSE_FILE down"
