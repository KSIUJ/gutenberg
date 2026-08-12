#!/bin/bash
set -e

TEST_NUM=$1

# Helper function to assert HTTP status codes
assert_status() {
    local actual="$1"
    local expected="$2"
    local description="$3"

    if [ "$actual" = "$expected" ]; then
        echo "✓ $description (got $actual)"
        return 0
    else
        echo "✗ $description (expected $expected, got $actual)"
        return 1
    fi
}

# Cleanup function
cleanup() {
    local compose_file="$1"
    echo ""
    echo "Cleaning up..."
    docker compose -f "$compose_file" down 2>/dev/null || true
}

# Run a single test
run_single_test() {
    local test_num="$1"
    local compose_file="docker-compose.test${test_num}-*.yml"

    echo "========================================="
    echo "Running Test Scenario $test_num"
    echo "========================================="
    echo ""

    # Cleanup any previous runs
    docker compose -f docker-compose.test*.yml down 2>/dev/null || true

    # Start containers
    docker compose -f "$compose_file" up -d

    # Wait for container to be ready (health check loop)
    echo "Waiting for nginx to start..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f "$compose_file" ps | grep -q "Up\|running"; then
            sleep 2  # Give nginx a moment to fully initialize
            break
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "✗ Container failed to start within ${max_attempts}s"
        docker compose -f "$compose_file" logs
        cleanup "$compose_file"
        return 1
    fi

    echo ""
    echo "Container logs:"
    echo "========================================="
    docker compose -f "$compose_file" logs
    echo "========================================="
    echo ""

    # Run test-specific checks
    local test_failed=0
    case $test_num in
        1)
            echo "Test 1: HTTP on port 8080 (SSL disabled)"
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "502" "HTTP Status (expected 502 = no backend)" || test_failed=1
            ;;
        2)
            echo "Test 2a: HTTP on port 8080"
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "502" "HTTP Status (expected 502 = no backend)" || test_failed=1
            echo ""
            echo "Test 2b: HTTPS on port 8443"
            STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "502" "HTTPS Status (expected 502 = no backend)" || test_failed=1
            ;;
        3)
            echo "Test 3a: HTTP should redirect (301)"
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "301" "HTTP Status (redirect to HTTPS)" || test_failed=1
            echo ""
            echo "Test 3b: HTTPS serves content"
            STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "502" "HTTPS Status (expected 502 = no backend)" || test_failed=1
            ;;
        4)
            echo "Test 4a: HSTS header presence"
            HSTS=$(curl -k -s -I https://localhost:8443/ 2>/dev/null | grep -i "strict-transport-security" | cut -d: -f2- | xargs)
            if [ -n "$HSTS" ]; then
                echo "✓ HSTS header found: $HSTS"
            else
                echo "✗ HSTS header not found"
                test_failed=1
            fi
            echo ""
            echo "Test 4b: HTTPS content"
            STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/ 2>/dev/null || echo "000")
            assert_status "$STATUS" "502" "HTTPS Status (expected 502 = no backend)" || test_failed=1
            ;;
        5)
            echo "Test 5: SSL with missing certificate"
            echo "Expected: Container should fail with clear error"
            sleep 2
            if docker compose -f "$compose_file" ps | grep -q "Up"; then
                echo "✗ Container is running (should have failed)"
                test_failed=1
            else
                echo "✓ Container failed as expected"
                echo ""
                echo "Error message:"
                docker compose -f "$compose_file" logs 2>&1 | grep -i "ERROR" | head -3
            fi
            ;;
        6)
            echo "Test 6: SSL with invalid protocol"
            echo "Expected: Container should fail with validation error"
            sleep 2
            if docker compose -f "$compose_file" ps | grep -q "Up"; then
                echo "✗ Container is running (should have failed)"
                test_failed=1
            else
                echo "✓ Container failed as expected"
                echo ""
                echo "Error message:"
                docker compose -f "$compose_file" logs 2>&1 | grep -i "ERROR" | head -3
            fi
            ;;
        *)
            echo "✗ Unknown test number: $test_num"
            cleanup "$compose_file"
            return 1
            ;;
    esac

    # Cleanup
    cleanup "$compose_file"

    if [ $test_failed -eq 1 ]; then
        echo ""
        echo "✗ Test $test_num FAILED"
        return 1
    else
        echo ""
        echo "✓ Test $test_num PASSED"
        return 0
    fi
}

if [ -z "$TEST_NUM" ]; then
    echo "Usage: $0 <test-number|all>"
    echo "Available tests:"
    echo "  1 - SSL Disabled (backward compatibility)"
    echo "  2 - SSL Dual-Mode (HTTP + HTTPS)"
    echo "  3 - SSL with HTTP→HTTPS Redirect"
    echo "  4 - SSL with HSTS"
    echo "  5 - SSL with missing certificate (error test)"
    echo "  6 - SSL with invalid protocol (error test)"
    echo "  all - Run all tests"
    exit 1
fi

# Run tests
if [ "$TEST_NUM" = "all" ]; then
    echo "Running all tests..."
    echo ""

    failed_tests=()
    for i in 1 2 3 4 5 6; do
        if ! run_single_test $i; then
            failed_tests+=($i)
        fi
        echo ""
    done

    echo "========================================="
    echo "Test Summary"
    echo "========================================="
    if [ ${#failed_tests[@]} -eq 0 ]; then
        echo "✓ All tests passed!"
        exit 0
    else
        echo "✗ Failed tests: ${failed_tests[*]}"
        exit 1
    fi
else
    # Run single test
    if ! run_single_test "$TEST_NUM"; then
        exit 1
    fi
    exit 0
fi
