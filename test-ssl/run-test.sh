#!/bin/bash
set -e

TEST_NUM=$1

if [ -z "$TEST_NUM" ]; then
    echo "Usage: $0 <test-number>"
    echo "Available tests:"
    echo "  1 - SSL Disabled (backward compatibility)"
    echo "  2 - SSL Dual-Mode (HTTP + HTTPS)"
    echo "  3 - SSL with HTTP→HTTPS Redirect"
    echo "  4 - SSL with HSTS"
    echo "  5 - SSL with missing certificate (error test)"
    echo "  6 - SSL with invalid protocol (error test)"
    exit 1
fi

COMPOSE_FILE="docker-compose.test${TEST_NUM}-*.yml"

echo "========================================="
echo "Running Test Scenario $TEST_NUM"
echo "========================================="
echo ""

docker compose -f docker-compose.test*.yml down 2>/dev/null || true

docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "Waiting for nginx to start..."
sleep 3

echo ""
echo "Container logs:"
echo "========================================="
docker compose -f "$COMPOSE_FILE" logs
echo "========================================="
echo ""

case $TEST_NUM in
    1)
        echo "Test 1: HTTP on port 8080 (SSL disabled)"
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
        echo "HTTP Status: $STATUS"
        [ "$STATUS" = "502" ] && echo "✓ Expected (no backend)" || echo "✗ Unexpected status"
        ;;
    2)
        echo "Test 2a: HTTP on port 8080"
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
        echo "HTTP Status: $STATUS"
        [ "$STATUS" = "502" ] && echo "✓ Expected (no backend)" || echo "✗ Unexpected status"
        echo ""
        echo "Test 2b: HTTPS on port 8443"
        STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
        echo "HTTPS Status: $STATUS"
        [ "$STATUS" = "502" ] && echo "✓ Expected (no backend)" || echo "✗ Unexpected status"
        ;;
    3)
        echo "Test 3a: HTTP should redirect (301)"
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
        echo "HTTP Status: $STATUS"
        [ "$STATUS" = "301" ] && echo "✓ Redirect OK" || echo "✗ Expected 301"
        echo ""
        echo "Test 3b: HTTPS serves content"
        STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
        echo "HTTPS Status: $STATUS"
        [ "$STATUS" = "502" ] && echo "✓ Expected (no backend)" || echo "✗ Unexpected status"
        ;;
    4)
        echo "Test 4a: HSTS header presence"
        HSTS=$(curl -k -s -I https://localhost:8443/ 2>/dev/null | grep -i "strict-transport-security" | cut -d: -f2- | xargs)
        if [ -n "$HSTS" ]; then
            echo "✓ HSTS header found: $HSTS"
        else
            echo "✗ HSTS header not found"
        fi
        echo ""
        echo "Test 4b: HTTPS content"
        STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
        echo "HTTPS Status: $STATUS"
        [ "$STATUS" = "502" ] && echo "✓ Expected (no backend)" || echo "✗ Unexpected status"
        ;;
    5)
        echo "Test 5: SSL with missing certificate"
        echo "Expected: Container should fail with clear error"
        sleep 2
        if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            echo "✗ Container is running (should have failed)"
        else
            echo "✓ Container failed as expected"
            echo ""
            echo "Error message:"
            docker compose -f "$COMPOSE_FILE" logs 2>&1 | grep -i "ERROR" | head -3
        fi
        ;;
    6)
        echo "Test 6: SSL with invalid protocol"
        echo "Expected: Container should fail with validation error"
        sleep 2
        if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            echo "✗ Container is running (should have failed)"
        else
            echo "✓ Container failed as expected"
            echo ""
            echo "Error message:"
            docker compose -f "$COMPOSE_FILE" logs 2>&1 | grep -i "ERROR" | head -3
        fi
        ;;
esac

echo ""
echo "Test completed. Container is still running."
echo "To stop: docker compose -f \"$COMPOSE_FILE\" down"
