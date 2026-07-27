#!/bin/sh
set -e

TRUSTED_IPS="${GUTENBERG_TRUSTED_PROXY_IPS:-172.17.0.0/16}"

# Check for forward-compatible warning (PR #175 variables)
if [ -z "$GUTENBERG_TRUSTED_PROXY_IPS" ]; then
    if [ "$GUTENBERG_TRUST_X_FORWARDED_HOST" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_FORWARDED_PROTO" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_REAL_IP" = "1" ]; then
        echo "WARNING: GUTENBERG_TRUST_* variables are enabled but GUTENBERG_TRUSTED_PROXY_IPS is not explicitly configured." >&2
        echo "Currently using default Docker bridge network (172.17.0.0/16) as trusted proxy." >&2
        echo "This may be insecure if running behind a different reverse proxy." >&2
        echo "Please set GUTENBERG_TRUSTED_PROXY_IPS explicitly for your deployment." >&2
    fi
fi

# Generate geo block to temp file
cat > /tmp/gutenberg-geo.conf <<EOF
geo \$remote_addr \$is_trusted_proxy {
    default 0;
EOF

# Parse comma or space separated list
echo "$TRUSTED_IPS" | tr ',' ' ' | xargs -n1 | while read -r ip; do
    [ -n "$ip" ] && echo "    $ip 1;" >> /tmp/gutenberg-geo.conf
done

echo "}" >> /tmp/gutenberg-geo.conf

# Concatenate geo + static config
cat /tmp/gutenberg-geo.conf /etc/nginx/gutenberg.conf.static > /etc/nginx/conf.d/gutenberg.conf
rm /tmp/gutenberg-geo.conf

echo "INFO: Configured trusted proxy IPs: $TRUSTED_IPS" >&2
