#!/bin/sh
set -e

# ========================================
# Environment Variable Defaults
# ========================================

# Check if SSL is enabled
if [ "$GUTENBERG_SSL_ENABLE" != "1" ]; then
    # SSL disabled - generate HTTP-only server block (backward compatible)
    cat > /tmp/gutenberg-servers.conf <<'EOF'
server {
    listen 80;

    # Log format and map defined at http level (from geo block)
    access_log /dev/stderr gutenberg_untrusted_proxy if=$untrusted_proxy_access;

    # Reject ALL requests from non-trusted sources
    if ($is_trusted_proxy = 0) {
        return 400;
    }

    include /etc/nginx/gutenberg-locations.d/*.conf;
}
EOF

    # Concatenate geo + HTTP server → final config
    cat /tmp/gutenberg-geo.conf /tmp/gutenberg-servers.conf > /etc/nginx/conf.d/gutenberg.conf
    rm /tmp/gutenberg-geo.conf /tmp/gutenberg-servers.conf

    echo "INFO: SSL disabled. Nginx listening on HTTP port 80 only." >&2
    exit 0
fi

# ========================================
# SSL Enabled - Validation
# ========================================

if [ -z "$GUTENBERG_SSL_CERT_PATH" ]; then
    echo "ERROR: GUTENBERG_SSL_ENABLE is set but GUTENBERG_SSL_CERT_PATH is not configured." >&2
    echo "You must specify the path to the SSL certificate file inside the container." >&2
    echo "Example: GUTENBERG_SSL_CERT_PATH=/etc/ssl/certs/gutenberg.crt" >&2
    echo "See: https://ksiuj.github.io/gutenberg/admin/docker.html#ssl-tls-configuration" >&2
    exit 1
fi

if [ -z "$GUTENBERG_SSL_KEY_PATH" ]; then
    echo "ERROR: GUTENBERG_SSL_ENABLE is set but GUTENBERG_SSL_KEY_PATH is not configured." >&2
    echo "You must specify the path to the SSL private key file inside the container." >&2
    echo "Example: GUTENBERG_SSL_KEY_PATH=/etc/ssl/certs/gutenberg.key" >&2
    echo "See: https://ksiuj.github.io/gutenberg/admin/docker.html#ssl-tls-configuration" >&2
    exit 1
fi

# Validate certificate files exist and are readable
if [ ! -f "$GUTENBERG_SSL_CERT_PATH" ]; then
    echo "ERROR: SSL certificate file not found: $GUTENBERG_SSL_CERT_PATH" >&2
    echo "Ensure the certificate file is mounted via Docker volumes." >&2
    exit 1
fi

if [ ! -r "$GUTENBERG_SSL_CERT_PATH" ]; then
    echo "ERROR: SSL certificate file exists but is not readable: $GUTENBERG_SSL_CERT_PATH" >&2
    echo "Check file permissions (should be at least 644)." >&2
    exit 1
fi

if [ ! -f "$GUTENBERG_SSL_KEY_PATH" ]; then
    echo "ERROR: SSL private key file not found: $GUTENBERG_SSL_KEY_PATH" >&2
    echo "Ensure the private key file is mounted via Docker volumes." >&2
    exit 1
fi

if [ ! -r "$GUTENBERG_SSL_KEY_PATH" ]; then
    echo "ERROR: SSL private key file exists but is not readable: $GUTENBERG_SSL_KEY_PATH" >&2
    echo "Check file permissions (should be at least 600)." >&2
    exit 1
fi

# ========================================
# Set Optional Defaults
# ========================================

: "${GUTENBERG_SSL_PORT:=443}"
: "${GUTENBERG_SSL_PROTOCOLS:=TLSv1.2 TLSv1.3}"
: "${GUTENBERG_SSL_HSTS_MAX_AGE:=31536000}"

# ========================================
# Generate HTTPS Server Block
# ========================================

cat > /tmp/gutenberg-servers.conf <<EOF
server {
    listen ${GUTENBERG_SSL_PORT} ssl;

    ssl_certificate ${GUTENBERG_SSL_CERT_PATH};
    ssl_certificate_key ${GUTENBERG_SSL_KEY_PATH};
    ssl_protocols ${GUTENBERG_SSL_PROTOCOLS};
EOF

# Add ssl_ciphers only if specified (otherwise use nginx defaults)
if [ -n "$GUTENBERG_SSL_CIPHERS" ]; then
    cat >> /tmp/gutenberg-servers.conf <<EOF
    ssl_ciphers ${GUTENBERG_SSL_CIPHERS};
EOF
fi

# Add HSTS header if enabled
if [ "$GUTENBERG_SSL_HSTS_ENABLE" = "1" ]; then
    HSTS_HEADER="Strict-Transport-Security \"max-age=${GUTENBERG_SSL_HSTS_MAX_AGE}"

    if [ "$GUTENBERG_SSL_HSTS_INCLUDE_SUBDOMAINS" = "1" ]; then
        HSTS_HEADER="${HSTS_HEADER}; includeSubDomains"
    fi

    if [ "$GUTENBERG_SSL_HSTS_PRELOAD" = "1" ]; then
        HSTS_HEADER="${HSTS_HEADER}; preload"
    fi

    HSTS_HEADER="${HSTS_HEADER}\""

    cat >> /tmp/gutenberg-servers.conf <<EOF
    add_header ${HSTS_HEADER} always;
EOF
fi

# Complete HTTPS server block
cat >> /tmp/gutenberg-servers.conf <<'EOF'

    # Log format and map defined at http level (from geo block)
    access_log /dev/stderr gutenberg_untrusted_proxy if=$untrusted_proxy_access;

    # Reject ALL requests from non-trusted sources
    if ($is_trusted_proxy = 0) {
        return 400;
    }

    include /etc/nginx/gutenberg-locations.d/*.conf;
}
EOF

# ========================================
# Generate HTTP Server Block
# ========================================

if [ "$GUTENBERG_SSL_REDIRECT_HTTP" = "1" ]; then
    # HTTP → HTTPS redirect mode
    cat >> /tmp/gutenberg-servers.conf <<EOF

server {
    listen 80;
    return 301 https://\$host\$request_uri;
}
EOF
    echo "INFO: SSL enabled on port ${GUTENBERG_SSL_PORT}. HTTP requests on port 80 will redirect to HTTPS." >&2
else
    # Dual mode: serve content on both HTTP and HTTPS
    cat >> /tmp/gutenberg-servers.conf <<'EOF'

server {
    listen 80;

    # Log format and map defined at http level (from geo block)
    access_log /dev/stderr gutenberg_untrusted_proxy if=$untrusted_proxy_access;

    # Reject ALL requests from non-trusted sources
    if ($is_trusted_proxy = 0) {
        return 400;
    }

    include /etc/nginx/gutenberg-locations.d/*.conf;
}
EOF
    echo "INFO: SSL enabled on port ${GUTENBERG_SSL_PORT}. HTTP port 80 also serves content (no redirect)." >&2
fi

# ========================================
# Final Concatenation
# ========================================

cat /tmp/gutenberg-geo.conf /tmp/gutenberg-servers.conf > /etc/nginx/conf.d/gutenberg.conf
rm /tmp/gutenberg-geo.conf /tmp/gutenberg-servers.conf

echo "INFO: SSL certificate: ${GUTENBERG_SSL_CERT_PATH}" >&2
echo "INFO: SSL protocols: ${GUTENBERG_SSL_PROTOCOLS}" >&2

if [ "$GUTENBERG_SSL_HSTS_ENABLE" = "1" ]; then
    echo "INFO: HSTS enabled with max-age=${GUTENBERG_SSL_HSTS_MAX_AGE}" >&2
fi
