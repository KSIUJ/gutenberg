#!/bin/sh
set -e

if [ -z "$GUTENBERG_TRUSTED_PROXY_IPS" ]; then
    # GUTENBERG_TRUSTED_PROXY_IPS is not set

    # Check if any GUTENBERG_TRUST_* variable is enabled
    if [ "$GUTENBERG_TRUST_X_FORWARDED_HOST" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_FORWARDED_PROTO" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_REAL_IP" = "1" ]; then
        echo "ERROR: GUTENBERG_TRUST_* variables are enabled but GUTENBERG_TRUSTED_PROXY_IPS is not configured." >&2
        echo "This is a security risk - Nginx would trust headers from any source IP." >&2
        echo "Please set GUTENBERG_TRUSTED_PROXY_IPS to restrict which proxies can set these headers." >&2
        exit 1
    fi

    # No trust variables enabled - allow all source IPs (no filtering needed)
    # This maintains backward compatibility with deployments that don't use a reverse proxy
    TRUSTED_IPS="0.0.0.0/0"
else
    # GUTENBERG_TRUSTED_PROXY_IPS is set - use it for filtering
    TRUSTED_IPS="$GUTENBERG_TRUSTED_PROXY_IPS"
fi

# Generate geo block to temp file
# Special case: when TRUSTED_IPS is 0.0.0.0/0, set default to 1 instead of listing it explicitly
# This avoids nginx warning about duplicate network "0.0.0.0/0"
if [ "$TRUSTED_IPS" = "0.0.0.0/0" ]; then
    cat > /tmp/gutenberg-geo.conf <<EOF
geo \$remote_addr \$is_trusted_proxy {
    default 1;
}
EOF
else
    cat > /tmp/gutenberg-geo.conf <<EOF
geo \$remote_addr \$is_trusted_proxy {
    default 0;
EOF

    # Parse comma or space separated list
    echo "$TRUSTED_IPS" | tr ',' ' ' | xargs -n1 | while read -r ip; do
        [ -n "$ip" ] && echo "    $ip 1;" >> /tmp/gutenberg-geo.conf
    done

    echo "}" >> /tmp/gutenberg-geo.conf
fi

# Concatenate geo + static config
cat /tmp/gutenberg-geo.conf /etc/nginx/gutenberg.conf.static > /etc/nginx/conf.d/gutenberg.conf
rm /tmp/gutenberg-geo.conf

echo "INFO: Configured trusted proxy IPs: $TRUSTED_IPS" >&2
