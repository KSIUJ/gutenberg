#!/bin/sh

# This script generates the /etc/nginx/gutenberg-locations.d/10-gutenberg-backend.conf
# configuration file, which proxies requests to the Django backend server,
# based on these environment variables specified at runtime:
# - `GUTENBERG_TRUST_X_FORWARDED_HOST`
# - `GUTENBERG_TRUST_X_FORWARDED_PROTO`
# - `GUTENBERG_TRUST_X_REAL_IP`

set -eu

if [ "${GUTENBERG_TRUST_X_FORWARDED_HOST:-}" != "0" ] && [ "${GUTENBERG_TRUST_X_FORWARDED_HOST:-}" != "1" ]; then
  echo "Error: GUTENBERG_TRUST_X_FORWARDED_HOST must be set to either 0 or 1." >&2
  exit 1
fi
if [ "${GUTENBERG_TRUST_X_FORWARDED_PROTO:-}" != "0" ] && [ "${GUTENBERG_TRUST_X_FORWARDED_PROTO:-}" != "1" ]; then
  echo "Error: GUTENBERG_TRUST_X_FORWARDED_PROTO must be set to either 0 or 1." >&2
  exit 1
fi
if [ "${GUTENBERG_TRUST_X_REAL_IP:-}" != "0" ] && [ "${GUTENBERG_TRUST_X_REAL_IP:-}" != "1" ]; then
  echo "Error: GUTENBERG_TRUST_X_REAL_IP must be set to either 0 or 1." >&2
  exit 1
fi

generate_config() {
  echo 'location / {'
  echo '    proxy_pass http://gutenberg-backend:8000;'
  echo ''
  echo '    # [`USE_X_FORWARDED_HOST`](https://docs.djangoproject.com/en/6.0/ref/settings/#use-x-forwarded-host)'
  echo '    # is enabled in `backend/gutenberg/settings/docker_base.py`'
  if [ "${GUTENBERG_TRUST_X_FORWARDED_PROTO}" = "1" ]; then
    echo '    proxy_set_header X-Forwarded-Host $http_x_forwarded_host;'
  else
    echo '    proxy_set_header X-Forwarded-Host $http_host;'
  fi
  echo ''
  echo '    # [`SECURE_PROXY_SSL_HEADER`](https://docs.djangoproject.com/en/6.0/ref/settings/#secure-proxy-ssl-header)'
  echo '    # is set to `('\''HTTP_X_FORWARDED_PROTO'\'', '\''https'\'')` in `backend/gutenberg/settings/docker_base.py`'
  if [ "${GUTENBERG_TRUST_X_FORWARDED_PROTO}" = "1" ]; then
    echo '    proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;'
  else
    echo '    proxy_set_header X-Forwarded-Proto $scheme;'
  fi
  echo ''
  if [ "${GUTENBERG_TRUST_X_REAL_IP}" = "1" ]; then
    echo '    proxy_set_header X-Real-IP $http_x_real_ip;'
  else
    echo '    proxy_set_header X-Real-IP $remote_addr;'
  fi
  echo '    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;'
  echo '}'
}

echo "Generating /etc/nginx/gutenberg-locations.d/10-gutenberg-backend.conf:"
generate_config | tee /etc/nginx/gutenberg-locations.d/10-gutenberg-backend.conf