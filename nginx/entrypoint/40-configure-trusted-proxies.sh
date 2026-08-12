#!/bin/sh

# This script generates /tmp/gutenberg-geo.conf, which defines the `$is_trusted_proxy`
# and `$is_not_trusted_proxy` variables using the `geo` directive from `ngx_http_geo_module`,
# based on the GUTENBERG_TRUSTED_PROXY_IPS environment variable specified at runtime.
# This configuration is later merged with server blocks by 50-configure-ssl.sh.
#
# The variable `$is_trusted_proxy` will be `1` when the request comes from an IP address
# range specified in GUTENBERG_TRUSTED_PROXY_IPS and `0` otherwise.
# `$is_not_trusted_proxy` will be `1` if and only if `$is_trusted_proxy` is `0`,
# and `0` otherwise.

set -e

if [ -z "$GUTENBERG_TRUSTED_PROXY_IPS" ]; then
    if [ "$GUTENBERG_TRUST_X_FORWARDED_HOST" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_FORWARDED_PROTO" = "1" ] || \
       [ "$GUTENBERG_TRUST_X_REAL_IP" = "1" ]; then
        echo "ERROR: At least one of the GUTENBERG_TRUST_* variables is enabled but GUTENBERG_TRUSTED_PROXY_IPS is not configured." >&2
        echo "Security risk: If nginx is accessible from the internet without IP filtering," >&2
        echo "malicious clients can send arbitrary X-Real-IP/X-Forwarded-* headers that nginx will blindly trust." >&2
        echo "This might allow IP spoofing or bypassing the ALLOWED_HOSTS setting." >&2
        echo "Set GUTENBERG_TRUSTED_PROXY_IPS to specify which proxy IPs are allowed to make requests." >&2
        echo "See: https://ksiuj.github.io/gutenberg/admin/docker.html#trusted-proxy-configuration" >&2
        exit 1
    fi

    TRUSTED_IPS="0.0.0.0/0"
else
    TRUSTED_IPS="$GUTENBERG_TRUSTED_PROXY_IPS"
fi

generate_config() {
  # Format inspired by Django's detailed error messages
  cat <<EOF
log_format gutenberg_untrusted_proxy '*** Untrusted Proxy Source *** '
                                      'Request Method: \$request_method | '
                                      'Request URL: \$scheme://\$http_host\$request_uri | '
                                      'Client IP: \$remote_addr | '
                                      'Error: Invalid request source IP address. '
                                      'You may need to add this IP to GUTENBERG_TRUSTED_PROXY_IPS. '
                                      'Currently trusted IPs: $TRUSTED_IPS | '
                                      'Server time: \$time_local';

map \$is_trusted_proxy \$is_not_trusted_proxy {
    0    1;
    default 0;
}
EOF

  # Special case: when TRUSTED_IPS is 0.0.0.0/0, set default to 1 instead of listing it explicitly
  # This avoids nginx warning about duplicate network "0.0.0.0/0"
  if [ "$TRUSTED_IPS" = "0.0.0.0/0" ]; then
      cat <<EOF
geo \$remote_addr \$is_trusted_proxy {
    default 1;
}
EOF
  else
      cat <<EOF
geo \$remote_addr \$is_trusted_proxy {
    default 0;
EOF

      # Support both comma and space separators
      echo "$TRUSTED_IPS" | tr ',' ' ' | xargs -n1 | while read -r ip; do
          [ -n "$ip" ] && echo "    $ip 1;"
      done

      echo "}"
  fi
}

echo "Generating /tmp/gutenberg-geo.conf for use by SSL configuration script:"
generate_config > /tmp/gutenberg-geo.conf
cat /tmp/gutenberg-geo.conf
echo "INFO: Configured trusted proxy IPs: $TRUSTED_IPS" >&2
